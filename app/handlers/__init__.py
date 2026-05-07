from app.handlers.commands import router as commands_router
from app.handlers.voice import router as voice_router
from app.handlers.documents import router as documents_router

__all__ = [
    "commands_router",
    "voice_router",
    "documents_router",
]
