"""
Modelos y configuración para proveedores LLM.

Define los tipos de proveedores soportados y cómo instanciarlos.
"""
from enum import Enum
from pydantic import BaseModel
from langchain_core.language_models import BaseLanguageModel


class LLMProvider(str, Enum):
    """Proveedores de lenguaje soportados.

    Usamos str como mixin para que sea serializable a JSON directamente.
    """
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class LLMConfig(BaseModel):
    """Configuración completa para instanciar un LLM.

    Todos los campos tienen valores por defecto sensibles.
    Cualquier campo puede sobreescribirse desde variables de entorno
    o desde la API.
    """
    provider: LLMProvider = LLMProvider.OLLAMA
    model: str = "llama3.1"
    temperature: float = 0.0
    max_tokens: int = 4096
    api_key: str | None = None
    base_url: str | None = None


def get_llm(config: LLMConfig) -> BaseLanguageModel:
    """Instancia el LLM adecuado según la configuración.

    Usa imports diferidos (dentro de la función) para que
    solo se importe la librería del proveedor que realmente se usa.
    Esto evita errores de import si no tenés instalado un provider.
    """
    match config.provider:
        case LLMProvider.OPENAI:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                api_key=config.api_key,
                base_url=config.base_url,
            )

        case LLMProvider.ANTHROPIC:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                api_key=config.api_key,
                base_url=config.base_url,
            )

        case LLMProvider.OLLAMA:
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=config.model,
                temperature=config.temperature,
                num_predict=config.max_tokens,
                base_url=config.base_url or "http://localhost:11434",
            )

        case _:
            raise ValueError(f"Proveedor LLM no soportado: {config.provider}")
