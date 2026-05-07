from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.core.database import async_session_maker
from app.services import CandidateService, DocumentService
from app.models.database import Candidate

router = Router()


@router.message(F.photo)
async def handle_photo(message: types.Message):
    """Handle photo messages - offer to attach to candidate"""
    # Get the highest resolution photo
    photo = message.photo[-1]
    
    # Check if this is a reply to a candidate card or message
    if message.reply_to_message:
        # Try to extract candidate ID from replied message
        # This is simplified - in production you'd store message_id -> candidate_id mapping
        await message.answer(
            "📷 Фото получено.\n"
            "Для привязки к кандидату используйте команду в карточке кандидата."
        )
        return
    
    # Ask which candidate to attach to
    async with async_session_maker() as session:
        candidate_service = CandidateService(session)
        candidates = await candidate_service.get_all(limit=5)
    
    if not candidates:
        await message.answer("📷 Фото получено, но в базе нет кандидатов для привязки.")
        return
    
    keyboard = []
    for c in candidates:
        keyboard.append([InlineKeyboardButton(
            text=c.full_name,
            callback_data=f"attach_photo_{c.id}"
        )])
    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_attach")])
    
    await message.answer(
        "📷 <b>К какому кандидату прикрепить фото?</b>\n"
        "(Это может быть билет, скриншот оплаты или другой документ)",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    
    # Store file_id for later use
    # In production, use FSM state to store this


@router.callback_query(F.data.startswith("attach_photo_"))
async def callback_attach_photo(callback: types.CallbackQuery):
    """Attach photo to candidate"""
    candidate_id = int(callback.data.split("_")[-1])
    
    # Get the photo from the replied message or last sent
    # This is simplified - in production you'd have the file_id from state
    await callback.answer("ℹ️ Функция требует доработки контекста", show_alert=True)


@router.callback_query(F.data == "cancel_attach")
async def callback_cancel_attach(callback: types.CallbackQuery):
    """Cancel photo attachment"""
    await callback.message.delete()
    await callback.answer("Отменено")
