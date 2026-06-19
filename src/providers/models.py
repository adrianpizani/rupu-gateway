from enum import Enum
from pydantic import BaseModel

class LLMProvider(str, Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"