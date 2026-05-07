from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.core.database import async_session_maker
from app.services import CandidateService, DocumentService, ReminderService, groq_service
from app.models.database import TicketStatus, MedicalStatus, ArrivalStatus, EducationStatus
from datetime import datetime, timedelta
import aiofiles
import os

router = Router()


def get_ticket_emoji(status: TicketStatus) -> str:
    """Get emoji for ticket status"""
    emojis = {
        TicketStatus.NEEDED: "🎫❓",  # Нужен
        TicketStatus.BOUGHT: "🎫✅",  # Куплен
        TicketStatus.ARRIVED: "🎫📍",  # Прибыл
    }
    return emojis.get(status, "🎫")


def get_medical_emoji(status: MedicalStatus) -> str:
    """Get emoji for medical status"""
    emojis = {
        MedicalStatus.NOT_STARTED: "🏥⏳",  # Не начато
        MedicalStatus.IN_PROGRESS: "🏥🔄",  # В процессе
        MedicalStatus.FIT: "🏥✅",  # Годен
        MedicalStatus.UNFIT: "🏥❌",  # Не годен
    }
    return emojis.get(status, "🏥")


def get_candidate_status_line(candidate) -> str:
    """Generate status line like: Иванов И.И. | 🎫✅ | 🏥⏳ | 🪖❌"""
    ticket_emoji = get_ticket_emoji(candidate.ticket_status)
    medical_emoji = get_medical_emoji(candidate.medical_status)
    
    education_emoji = "🪖⏳"
    if candidate.education_status:
        education_emoji = "🪖✅" if candidate.education_status == EducationStatus.DEPARTED else "🪖📋"
    
    return f"{ticket_emoji} | {medical_emoji} | {education_emoji}"


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command"""
    await message.answer(
        "🫡 <b>Контракт-61: Диспетчер</b>\n\n"
        "Система управления кандидатами активна.\n\n"
        "<b>Возможности:</b>\n"
        "• Голосовой ввод — отправь голосовое сообщение\n"
        "• Быстрое добавление — /add\n"
        "• Список кандидатов — /list\n"
        "• Напоминания — /remind\n\n"
        "Готов к работе, товарищ!"
    )


@router.message(Command("add"))
async def cmd_add(message: types.Message, state: FSMContext):
    """Quick add candidate - smart form"""
    await message.answer(
        "📝 <b>Быстрое добавление кандидата</b>\n\n"
        "Введите данные одной строкой:\n"
        "<code>ФИО Телефон Источник</code>\n\n"
        "Пример:\n"
        "<code>Петров Иван 89991234567 Реклама_ТГ</code>\n\n"
        "Отправьте /cancel для отмены"
    )
    await state.set_state("waiting_for_candidate_data")


@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    """Cancel current operation"""
    await state.clear()
    await message.answer("❌ Операция отменена.")


@router.message(Command("list"))
async def cmd_list(message: types.Message):
    """Show all candidates"""
    async with async_session_maker() as session:
        service = CandidateService(session)
        candidates = await service.get_all(limit=20)
    
    if not candidates:
        await message.answer("📭 База пуста. Добавьте первого кандидата!")
        return
    
    text = "📋 <b>Последние кандидаты:</b>\n\n"
    for c in candidates[:10]:
        status_line = get_candidate_status_line(c)
        text += f"<b>{c.full_name}</b> | {status_line}\n"
        text += f"└─ {c.source} | {c.created_at.strftime('%d.%m %H:%M')}\n\n"
    
    if len(candidates) > 10:
        text += f"... и ещё {len(candidates) - 10} кандидатов"
    
    await message.answer(text)


@router.message(Command("search"))
async def cmd_search(message: types.Message):
    """Search candidate by name"""
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("🔍 Использование: /search Фамилия\nПример: /search Иванов")
        return
    
    query = args[1]
    
    async with async_session_maker() as session:
        service = CandidateService(session)
        candidates = await service.search_by_name(query)
    
    if not candidates:
        await message.answer(f"🔍 По запросу \"{query}\" ничего не найдено.")
        return
    
    text = f"🔍 <b>Найдено по запросу \"{query}\":</b>\n\n"
    for c in candidates:
        status_line = get_candidate_status_line(c)
        text += f"<b>{c.full_name}</b> | {status_line}\n"
        text += f"└─ 📞 {c.phone or 'Не указан'} | {c.source}\n\n"
    
    await message.answer(text)


@router.message(Command("remind"))
async def cmd_remind(message: types.Message):
    """Create reminder"""
    await message.answer(
        "⏰ <b>Создание напоминания</b>\n\n"
        "Голосовая команда:\n"
        "<i>\"Напомни проверить Петрова завтра в 10 утра\"</i>\n\n"
        "Или текстом:\n"
        "<code>/remind Петров завтра 10:00 Проверить статус билета</code>"
    )


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Show help"""
    await message.answer(
        "📚 <b>Справка по системе</b>\n\n"
        "<b>Команды:</b>\n"
        "/start — Главное меню\n"
        "/add — Быстрое добавление\n"
        "/list — Список кандидатов\n"
        "/search — Поиск по фамилии\n"
        "/remind — Напоминание\n"
        "/help — Эта справка\n\n"
        "<b>Голосовые команды:</b>\n"
        "• \"Запиши Алексея, 8900..., пришел с рекламы\"\n"
        "• \"Иванову купили билет на завтра\"\n"
        "• \"Сидоров прошел врачей, годен\"\n"
        "• \"Напомни проверить Петрова в понедельник\"\n\n"
        "<b>Кнопки в карточке:</b>\n"
        "🎫 Билет — циклическое переключение статуса\n"
        "🏥 Мед — статус медицины\n"
        "🖼 Документы — прикрепить/просмотреть файлы"
    )


@router.message(Command("test_voice"))
async def cmd_test_voice(message: types.Message):
    """Test voice transcription (debug)"""
    await message.answer(
        "🎤 Тест голоса:\n"
        "Отправьте голосовое сообщение, и я покажу результат транскрибации."
    )
