from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Bot Configuration
    bot_token: str
    groq_api_key: str
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./data/contract61.db"
    
    # Proxy (optional)
    http_proxy: str | None = None
    socks5_proxy: str | None = None
    
    # Admin IDs
    admin_ids: str = ""
    
    # Groq Models
    whisper_model: str = "whisper-large-v3-turbo"
    llm_model: str = "llama-3.3-70b-versatile"
    
    # Timezone
    timezone: str = "Europe/Moscow"
    
    @property
    def admin_id_list(self) -> List[int]:
        if not self.admin_ids:
            return []
        return [int(x.strip()) for x in self.admin_ids.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
