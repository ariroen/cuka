from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from app.core.database import async_session_maker
from app.services import CandidateService, DocumentService, ReminderService, groq_service
from app.models.database import TicketStatus, MedicalStatus, ArrivalStatus, EducationStatus
from datetime import datetime, timedelta
import aiofiles
import os
import tempfile

router = Router()


def parse_relative_date(date_str: str) -> datetime | None:
    """Parse relative date strings like 'завтра', 'послезавтра', 'в понедельник'"""
    if not date_str:
        return None
    
    now = datetime.utcnow()
    date_str = date_str.lower().strip()
    
    if "завтра" in date_str:
        return now + timedelta(days=1)
    elif "послезавтра" in date_str:
        return now + timedelta(days=2)
    elif "сегодня" in date_str:
        return now
    elif "понедельник" in date_str:
        days_ahead = 0 - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return now + timedelta(days=days_ahead)
    elif "вторник" in date_str:
        days_ahead = 1 - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return now + timedelta(days=days_ahead)
    elif "среда" in date_str or "среду" in date_str:
        days_ahead = 2 - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return now + timedelta(days=days_ahead)
    elif "четверг" in date_str or "четверг" in date_str:
        days_ahead = 3 - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return now + timedelta(days=days_ahead)
    elif "пятниц" in date_str:
        days_ahead = 4 - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return now + timedelta(days=days_ahead)
    elif "суббот" in date_str:
        days_ahead = 5 - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return now + timedelta(days=days_ahead)
    elif "воскресень" in date_str:
        days_ahead = 6 - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return now + timedelta(days=days_ahead)
    elif "недел" in date_str or "неделю" in date_str:
        return now + timedelta(weeks=1)
    elif "месяц" in date_str:
        return now + timedelta(days=30)
    
    return None


async def process_ai_intent(message: types.Message, intent_data: dict):
    """Process AI-analyzed intent and execute actions"""
    action = intent_data.get("action", "unknown")
    data = intent_data.get("data", {})
    confidence = intent_data.get("confidence", 0.0)
    
    async with async_session_maker() as session:
        candidate_service = CandidateService(session)
        document_service = DocumentService(session)
        reminder_service = ReminderService(session)
        
        candidate = None
        is_new = False
        
        # Find or create candidate if name provided
        if "full_name" in data:
            candidate, is_new = await candidate_service.find_or_create_by_name(
                full_name=data["full_name"],
                phone=data.get("phone"),
                source=data.get("source", "Прямой вход"),
            )
        
        response_text = ""
        
        if action == "create_candidate":
            if candidate and is_new:
                response_text = f"✅ <b>Кандидат создан:</b>\n{candidate.full_name}\n"
                if candidate.phone:
                    response_text += f"📞 {candidate.phone}\n"
                response_text += f"📌 Источник: {candidate.source}\n"
                
                # Apply additional status updates from the same message
                if "ticket_status" in data:
                    status_map = {"needed": TicketStatus.NEEDED, "bought": TicketStatus.BOUGHT, "arrived": TicketStatus.ARRIVED}
                    if data["ticket_status"] in status_map:
                        await candidate_service.update_ticket_status(candidate.id, status_map[data["ticket_status"]])
                        response_text += f"🎫 Статус билета: {data['ticket_status']}\n"
                
                if "medical_status" in data:
                    status_map = {"not_started": MedicalStatus.NOT_STARTED, "in_progress": MedicalStatus.IN_PROGRESS, "fit": MedicalStatus.FIT, "unfit": MedicalStatus.UNFIT}
                    if data["medical_status"] in status_map:
                        await candidate_service.update_medical_status(candidate.id, status_map[data["medical_status"]])
                        response_text += f"🏥 Статус медицины: {data['medical_status']}\n"
            elif candidate:
                response_text = f"ℹ️ Кандидат {candidate.full_name} уже существует в базе."
            else:
                response_text = "❌ Не удалось создать кандидата."
        
        elif action == "update_ticket":
            if candidate:
                status_map = {"needed": TicketStatus.NEEDED, "bought": TicketStatus.BOUGHT, "arrived": TicketStatus.ARRIVED}
                ticket_date = parse_relative_date(data.get("ticket_date", ""))
                
                if "ticket_status" in data and data["ticket_status"] in status_map:
                    await candidate_service.update_ticket_status(
                        candidate.id,
                        status_map[data["ticket_status"]],
                        ticket_date,
                    )
                    response_text = f"✅ <b>Билет обновлен:</b>\n{candidate.full_name}\n"
                    response_text += f"Статус: {data['ticket_status']}\n"
                    if ticket_date:
                        response_text += f"Дата: {ticket_date.strftime('%d.%m.%Y')}\n"
                else:
                    response_text = f"ℹ️ Кандидат найден: {candidate.full_name}, но статус билета не указан."
            else:
                response_text = "❌ Кандидат не найден. Уточните ФИО."
        
        elif action == "update_medical":
            if candidate:
                status_map = {"not_started": MedicalStatus.NOT_STARTED, "in_progress": MedicalStatus.IN_PROGRESS, "fit": MedicalStatus.FIT, "unfit": MedicalStatus.UNFIT}
                
                if "medical_status" in data and data["medical_status"] in status_map:
                    await candidate_service.update_medical_status(candidate.id, status_map[data["medical_status"]])
                    status_ru = {"not_started": "Не начато", "in_progress": "В процессе", "fit": "Годен ✅", "unfit": "Не годен ❌"}
                    response_text = f"✅ <b>Медицина обновлена:</b>\n{candidate.full_name}\n"
                    response_text += f"Статус: {status_ru.get(data['medical_status'], data['medical_status'])}\n"
                else:
                    response_text = f"ℹ️ Кандидат найден: {candidate.full_name}, но статус медицины не ясен."
            else:
                response_text = "❌ Кандидат не найден. Уточните ФИО."
        
        elif action == "set_reminder":
            if candidate:
                reminder_time_str = data.get("reminder_time", "")
                reminder_time = parse_relative_date(reminder_time_str)
                
                if not reminder_time:
                    reminder_time = datetime.utcnow() + timedelta(hours=2)
                
                reminder_message = data.get("reminder_message", f"Проверить {candidate.full_name}")
                
                await reminder_service.create_reminder(
                    candidate.id,
                    reminder_message,
                    reminder_time,
                )
                
                response_text = f"⏰ <b>Напоминание создано:</b>\n"
                response_text += f"Кандидат: {candidate.full_name}\n"
                response_text += f"Когда: {reminder_time.strftime('%d.%m.%Y %H:%M')}\n"
                response_text += f"Что: {reminder_message}\n"
            else:
                response_text = "❌ Не удалось создать напоминание — кандидат не найден."
        
        elif action == "add_note":
            if candidate:
                notes = data.get("notes", "")
                candidate.notes = (candidate.notes or "") + "\n" + notes if candidate.notes else notes
                response_text = f"📝 <b>Заметка добавлена:</b>\n{candidate.full_name}\n"
            else:
                response_text = "❌ Кандидат не найден."
        
        else:
            response_text = f"🤔 <b>Получено:</b>\n{text}\n\n"
            response_text += f"⚠️ Действие не распознано (уверенность: {confidence:.0%})\n"
            response_text += "Попробуйте сказать четче или используйте команды."
        
        if confidence < 0.5 and action != "unknown":
            response_text += f"\n\n⚠️ <i>Низкая уверенность распознавания ({confidence:.0%}). Проверьте результат.</i>"
        
        return response_text


@router.message(F.voice)
async def handle_voice_message(message: types.Message, state: FSMContext):
    """Handle voice messages - transcribe and analyze"""
    status_msg = await message.answer("🎤 Обрабатываю голосовое сообщение...")
    
    try:
        # Download voice message
        file = await message.bot.get_file(message.voice.file_id)
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp_file:
            await file.download(destination=tmp_file.name)
            tmp_path = tmp_file.name
        
        # Transcribe with Whisper
        text = await groq_service.transcribe_audio(tmp_path)
        
        # Clean up
        os.unlink(tmp_path)
        
        await status_msg.edit_text(f"📝 <b>Распознано:</b>\n<i>{text}</i>\n\n🧠 Анализирую намерение...")
        
        # Analyze intent with LLM
        intent_data = await groq_service.analyze_intent(text)
        
        # Process and respond
        response = await process_ai_intent(message, intent_data)
        
        await status_msg.edit_text(response)
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка обработки: {e}")


@router.message(F.audio)
async def handle_audio_message(message: types.Message):
    """Handle audio messages (sent as file)"""
    await message.answer(
        "🎵 Аудиофайл получен.\n"
        "Для голосовых команд используйте <b>голосовые сообщения</b> (микрофон), а не аудиофайлы."
    )
