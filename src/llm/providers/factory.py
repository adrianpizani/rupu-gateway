"""
Fábrica de LLMs con caché de instancias.

Reusa instancias de LLM para evitar el overhead de crear
nuevas conexiones en cada llamada.
"""
from langchain_core.language_models import BaseLanguageModel

from src.llm.providers.models import LLMConfig, get_llm


class LLMFactory:
    """Fábrica singleton de LLMs.

    Mantiene un caché de instancias indexadas por proveedor:modelo.
    Así, si dos stages usan el mismo modelo, comparten la misma instancia.

    Uso:
        llm = LLMFactory.get_llm(LLMConfig(provider="ollama", model="llama3.1"))
    """

    _instances: dict[str, BaseLanguageModel] = {}

    @classmethod
    def get_llm(cls, config: LLMConfig) -> BaseLanguageModel:
        """Retorna (o crea y cachea) un LLM según la configuración."""
        # Clave única por combinación provider:modelo
        # (no incluimos temperature/api_key porque no justifican una
        #  instancia separada a menos que cambien frecuentemente)
        key = f"{config.provider.value}:{config.model}"

        if key not in cls._instances:
            cls._instances[key] = get_llm(config)

        return cls._instances[key]

    @classmethod
    def clear_cache(cls):
        """Limpia el caché de instancias. Útil para tests."""
        cls._instances.clear()
