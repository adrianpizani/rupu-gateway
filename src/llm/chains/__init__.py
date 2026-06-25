"""Chains de LangChain para etapas del pipeline.

Las tres chains se importan explícitamente para que el decorador
``@ChainRegistry.register(...)`` se ejecute y llene el registro.
Sin estos imports, ``ChainRegistry._chains`` queda vacío y
``get_chain("extract", llm)`` falla en runtime.
"""
from src.llm.chains import extraction_chain  # noqa: F401  → register("extract")
from src.llm.chains import analysis_chain  # noqa: F401  → register("analyze")
from src.llm.chains import enrichment_chain  # noqa: F401  → register("enrich")

from src.llm.chains.base import BaseLLMChain
from src.llm.chains.registry import ChainRegistry

__all__ = ["ChainRegistry", "BaseLLMChain"]
