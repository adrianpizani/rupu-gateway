from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # Database settings
    SQLITE_DB: str = "rupu.db"

    @property
    def DB_URL(self) -> str:
        return os.getenv("DATABASE_URL", f"sqlite:///./{self.SQLITE_DB}")

settings = Settings()