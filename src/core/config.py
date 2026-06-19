from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # Database settings
    SQLITE_DB: str = "rupu.db"

    DEFAULT_LLM_PROVIDER: str = "ollama"

    OPENAI_API_KEY: str = ""
    OPENAI_MODOEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str = ""

    OLLAMA_MODOEL: str = "llama3.1"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    LLM_TEMPERATURE: float = 4.0
    LLM_MAX_TOKENS: int = 4096

    @property
    def DB_URL(self) -> str:
        return os.getenv("DATABASE_URL", f"sqlite:///./{self.SQLITE_DB}")

settings = Settings()