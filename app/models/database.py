from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class TicketStatus(enum.Enum):
    NEEDED = "needed"  # Нужен
    BOUGHT = "bought"  # Куплен
    ARRIVED = "arrived"  # Прибыл


class MedicalStatus(enum.Enum):
    NOT_STARTED = "not_started"  # Не начато
    IN_PROGRESS = "in_progress"  # В процессе
    FIT = "fit"  # Годен ✅
    UNFIT = "unfit"  # Не годен ❌


class ArrivalStatus(enum.Enum):
    EXPECTED = "expected"  # Ожидаем
    EN_ROUTE = "en_route"  # В пути
    ARRIVED = "arrived"  # Прибыл в Ростов


class EducationStatus(enum.Enum):
    ASSIGNED = "assigned"  # Распределен
    DEPARTED = "departed"  # Убыл в часть


class Candidate(Base):
    __tablename__ = "candidates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Basic info
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    
    # Source tracking
    source = Column(String(255), default="Прямой вход")
    
    # Ticket status
    ticket_status = Column(SQLEnum(TicketStatus), default=TicketStatus.NEEDED)
    ticket_date = Column(DateTime, nullable=True)
    
    # Arrival status
    arrival_status = Column(SQLEnum(ArrivalStatus), default=ArrivalStatus.EXPECTED)
    arrival_date = Column(DateTime, nullable=True)
    
    # Medical status
    medical_status = Column(SQLEnum(MedicalStatus), default=MedicalStatus.NOT_STARTED)
    
    # Education status
    education_status = Column(SQLEnum(EducationStatus), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Notes and additional info
    notes = Column(Text, nullable=True)
    
    # Relationships
    documents = relationship("Document", back_populates="candidate", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="candidate", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Candidate(id={self.id}, name='{self.full_name}', ticket={self.ticket_status.value}, medical={self.medical_status.value})>"


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    
    # Document type: ticket, payment, other
    doc_type = Column(String(50), default="ticket")
    
    # File ID in Telegram
    file_id = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    
    # OCR extracted text (optional)
    ocr_text = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    candidate = relationship("Candidate", back_populates="documents")
    
    def __repr__(self):
        return f"<Document(id={self.id}, candidate_id={self.candidate_id}, type={self.doc_type})>"


class Reminder(Base):
    __tablename__ = "reminders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    
    # Reminder text
    message = Column(Text, nullable=False)
    
    # When to remind
    remind_at = Column(DateTime, nullable=False)
    
    # Is it sent?
    is_sent = Column(Integer, default=0)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    candidate = relationship("Candidate", back_populates="reminders")
    
    def __repr__(self):
        return f"<Reminder(id={self.id}, candidate_id={self.candidate_id}, at={self.remind_at})>"
