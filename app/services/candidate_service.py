from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import Candidate, Document, Reminder, TicketStatus, MedicalStatus, ArrivalStatus, EducationStatus
from datetime import datetime
from typing import Optional, List


class CandidateService:
    """Service for candidate CRUD operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_candidate(
        self,
        full_name: str,
        phone: Optional[str] = None,
        source: str = "Прямой вход",
        ticket_status: TicketStatus = TicketStatus.NEEDED,
        notes: Optional[str] = None,
    ) -> Candidate:
        """Create a new candidate"""
        candidate = Candidate(
            full_name=full_name,
            phone=phone,
            source=source,
            ticket_status=ticket_status,
            notes=notes,
        )
        self.session.add(candidate)
        await self.session.flush()
        return candidate
    
    async def get_by_id(self, candidate_id: int) -> Optional[Candidate]:
        """Get candidate by ID"""
        result = await self.session.execute(
            select(Candidate).where(Candidate.id == candidate_id)
        )
        return result.scalar_one_or_none()
    
    async def search_by_name(self, name_part: str) -> List[Candidate]:
        """Search candidates by name (partial match)"""
        result = await self.session.execute(
            select(Candidate)
            .where(func.lower(Candidate.full_name).contains(func.lower(name_part)))
            .order_by(Candidate.created_at.desc())
            .limit(10)
        )
        return list(result.scalars().all())
    
    async def get_all(self, limit: int = 50) -> List[Candidate]:
        """Get all candidates (latest first)"""
        result = await self.session.execute(
            select(Candidate)
            .order_by(Candidate.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def update_ticket_status(
        self,
        candidate_id: int,
        status: TicketStatus,
        ticket_date: Optional[datetime] = None,
    ) -> Optional[Candidate]:
        """Update candidate's ticket status"""
        candidate = await self.get_by_id(candidate_id)
        if candidate:
            candidate.ticket_status = status
            if ticket_date:
                candidate.ticket_date = ticket_date
        return candidate
    
    async def update_medical_status(
        self,
        candidate_id: int,
        status: MedicalStatus,
    ) -> Optional[Candidate]:
        """Update candidate's medical status"""
        candidate = await self.get_by_id(candidate_id)
        if candidate:
            candidate.medical_status = status
        return candidate
    
    async def update_arrival_status(
        self,
        candidate_id: int,
        status: ArrivalStatus,
        arrival_date: Optional[datetime] = None,
    ) -> Optional[Candidate]:
        """Update candidate's arrival status"""
        candidate = await self.get_by_id(candidate_id)
        if candidate:
            candidate.arrival_status = status
            if arrival_date:
                candidate.arrival_date = arrival_date
        return candidate
    
    async def update_education_status(
        self,
        candidate_id: int,
        status: EducationStatus,
    ) -> Optional[Candidate]:
        """Update candidate's education status"""
        candidate = await self.get_by_id(candidate_id)
        if candidate:
            candidate.education_status = status
        return candidate
    
    async def find_or_create_by_name(
        self,
        full_name: str,
        phone: Optional[str] = None,
        source: str = "Прямой вход",
    ) -> tuple[Candidate, bool]:
        """Find candidate by name or create new one. Returns (candidate, is_new)"""
        # Try to find by exact name match first
        result = await self.session.execute(
            select(Candidate).where(Candidate.full_name == full_name)
        )
        candidate = result.scalar_one_or_none()
        
        if candidate:
            return candidate, False
        
        # Try partial match
        result = await self.session.execute(
            select(Candidate)
            .where(func.lower(Candidate.full_name).contains(func.lower(full_name.split()[0])))
            .limit(1)
        )
        candidate = result.scalar_one_or_none()
        
        if candidate:
            return candidate, False
        
        # Create new
        candidate = await self.create_candidate(
            full_name=full_name,
            phone=phone,
            source=source,
        )
        return candidate, True


class DocumentService:
    """Service for document management"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def add_document(
        self,
        candidate_id: int,
        file_id: str,
        doc_type: str = "ticket",
        file_path: Optional[str] = None,
        ocr_text: Optional[str] = None,
    ) -> Document:
        """Add document to candidate"""
        document = Document(
            candidate_id=candidate_id,
            file_id=file_id,
            doc_type=doc_type,
            file_path=file_path,
            ocr_text=ocr_text,
        )
        self.session.add(document)
        await self.session.flush()
        return document
    
    async def get_documents(self, candidate_id: int) -> List[Document]:
        """Get all documents for candidate"""
        result = await self.session.execute(
            select(Document)
            .where(Document.candidate_id == candidate_id)
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())


class ReminderService:
    """Service for reminder management"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_reminder(
        self,
        candidate_id: int,
        message: str,
        remind_at: datetime,
    ) -> Reminder:
        """Create a new reminder"""
        reminder = Reminder(
            candidate_id=candidate_id,
            message=message,
            remind_at=remind_at,
        )
        self.session.add(reminder)
        await self.session.flush()
        return reminder
    
    async def get_pending_reminders(self) -> List[Reminder]:
        """Get all unsent reminders that are due"""
        now = datetime.utcnow()
        result = await self.session.execute(
            select(Reminder)
            .where(Reminder.is_sent == 0)
            .where(Reminder.remind_at <= now)
            .order_by(Reminder.remind_at)
        )
        return list(result.scalars().all())
    
    async def mark_sent(self, reminder_id: int):
        """Mark reminder as sent"""
        result = await self.session.execute(
            select(Reminder).where(Reminder.id == reminder_id)
        )
        reminder = result.scalar_one_or_none()
        if reminder:
            reminder.is_sent = 1
