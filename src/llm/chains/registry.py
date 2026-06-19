"""Registro central de chains de LangChain.

Patrón Registry: las chains se auto-registran con un decorador,
permitiendo agregar nuevas operaciones sin modificar el pipeline.
"""
from langchain_core.language_models import BaseLanguageModel

from src.llm.chains.base import BaseLLMChain


class ChainRegistry:
    """Registro de chains disponibles.

    Cada chain se registra con un nombre único usando el decorador
    ``@ChainRegistry.register("nombre")``.

    Uso:
        @ChainRegistry.register("extract")
        class ExtractionChain(BaseLLMChain):
            ...

        # En el pipeline:
        chain = ChainRegistry.get_chain("extract", llm)
        result = await chain.process(data)
    """

    _chains: dict[str, type[BaseLLMChain]] = {}

    @classmethod
    def register(cls, name: str):
        """Decorador: registra una chain class bajo un nombre."""
        def wrapper(chain_class: type[BaseLLMChain]) -> type[BaseLLMChain]:
            cls._chains[name] = chain_class
            return chain_class
        return wrapper

    @classmethod
    def get_chain(cls, name: str, llm: BaseLanguageModel) -> BaseLLMChain:
        """Retorna una instancia de la chain registrada con el nombre dado."""
        if name not in cls._chains:
            raise ValueError(
                f"Chain '{name}' no registrada. "
                f"Disponibles: {', '.join(cls.list_chains())}"
            )
        return cls._chains[name](llm)

    @classmethod
    def list_chains(cls) -> list[str]:
        """Lista los nombres de todas las chains registradas."""
        return list(cls._chains.keys())

    @classmethod
    def clear(cls):
        """Limpia el registro. Útil para tests."""
        cls._chains.clear()
