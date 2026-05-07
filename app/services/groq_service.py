from groq import Groq, AsyncGroq
from app.core.config import settings


class GroqService:
    """Service for interacting with Groq API (Whisper + LLM)"""
    
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.groq_api_key)
        self.whisper_model = settings.whisper_model
        self.llm_model = settings.llm_model
    
    async def transcribe_audio(self, audio_file_path: str) -> str:
        """Transcribe voice message to text using Whisper"""
        try:
            with open(audio_file_path, "rb") as file:
                transcription = await self.client.audio.transcriptions.create(
                    file=(audio_file_path, file.read()),
                    model=self.whisper_model,
                    language="ru",
                )
            return transcription.text
        except Exception as e:
            raise Exception(f"Transcription error: {e}")
    
    async def analyze_intent(self, text: str) -> dict:
        """Analyze text intent using Llama 3.3"""
        
        mega_prompt = """
Ты — интеллектуальный ассистент военной диспетчерской системы "Контракт-61".
Твоя задача — анализировать входящие сообщения и извлекать структурированные данные.

ВОЗМОЖНЫЕ ДЕЙСТВИЯ:
1. create_candidate — Создать нового кандидата
2. update_ticket — Обновить статус билета
3. update_medical — Обновить статус медицины
4. update_arrival — Обновить статус прибытия
5. set_reminder — Установить напоминание
6. add_note — Добавить заметку

ИЗВЛЕКАЕМЫЕ ПОЛЯ:
- full_name: ФИО кандидата (фамилия имя отчество или фамилия инициалы)
- phone: номер телефона в формате 89XXXXXXXXX
- source: источник прихода (Реклама, Прямой вход, Знакомые, и т.д.)
- ticket_status: статус билета (needed/bought/arrived)
- ticket_date: дата билета (если упомянута)
- arrival_date: дата прибытия
- medical_status: статус медицины (not_started/in_progress/fit/unfit)
- reminder_time: время напоминания (завтра, через 2 часа, в понедельник в 9 утра)
- reminder_message: текст напоминания
- notes: дополнительные заметки

ПРАВИЛА:
- Если упоминается "купил билет", "взяли билет" → ticket_status = bought
- Если "прибыл", "приедет" → arrival_status相关
- Если "прошел врачей", "годен" → medical_status = fit
- Если "не годен", "отказ" → medical_status = unfit
- Источники: "с рекламы", "канал", "таргет" → source = Реклама
- Даты: "завтра", "послезавтра", "в понедельник", "через неделю" — парсить относительно сегодня

ФОРМАТ ОТВЕТА — ТОЛЬКО JSON:
{
    "action": "действие",
    "data": {
        "field": "value"
    },
    "confidence": 0.0-1.0
}

ПРИМЕР 1:
Вход: "Запиши Алексея, 89001234567, пришел с рекламы, билет купили"
Выход: {"action": "create_candidate", "data": {"full_name": "Алексей", "phone": "89001234567", "source": "Реклама", "ticket_status": "bought"}, "confidence": 0.95}

ПРИМЕР 2:
Вход: "Иванову купили билет на завтра"
Выход: {"action": "update_ticket", "data": {"full_name": "Иванов", "ticket_status": "bought", "ticket_date": "завтра"}, "confidence": 0.9}

ПРИМЕР 3:
Вход: "Сидоров прошел врачей, всё в порядке"
Выход: {"action": "update_medical", "data": {"full_name": "Сидоров", "medical_status": "fit"}, "confidence": 0.92}

ПРИМЕР 4:
Вход: "Напомни проверить Петрова завтра в 10 утра"
Выход: {"action": "set_reminder", "data": {"full_name": "Петров", "reminder_time": "завтра в 10:00", "reminder_message": "Проверить Петрова"}, "confidence": 0.93}

Теперь проанализируй это сообщение:
""" + text

        try:
            response = await self.client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "Ты — структурированный JSON-парсер. Отвечай ТОЛЬКО валидным JSON без markdown."},
                    {"role": "user", "content": mega_prompt}
                ],
                temperature=0.1,
                max_tokens=500,
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Clean markdown if present
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            import json
            return json.loads(result_text)
            
        except Exception as e:
            return {
                "action": "unknown",
                "data": {},
                "confidence": 0.0,
                "error": str(e)
            }


groq_service = GroqService()
