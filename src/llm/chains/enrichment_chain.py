"""
Chain de enriquecimiento de datos usando un LLM.

Toma datos analizados y genera: tags, acciones sugeridas y
resumen ejecutivo. Retorna JSON.
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.llm.chains.base import BaseLLMChain
from src.llm.chains.registry import ChainRegistry


ENRICHMENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Eres un especialista en enriquecimiento de datos. "
               "Del texto proporcionado, genera:\n"
               "1. Tags/relevancia (3-5 tags representativos)\n"
               "2. Acciones sugeridas (qué se podría hacer con esta información)\n"
               "3. Resumen ejecutivo de dos oraciones\n\n"
               "Responde ÚNICAMENTE con un objeto JSON válido, sin explicaciones."),
    ("human", "{text}"),
])


@ChainRegistry.register("enrich")
class EnrichmentChain(BaseLLMChain):
    """Chain que enriquece datos generando tags, acciones y resumen ejecutivo."""

    async def process(self, data: str) -> str:
        chain = ENRICHMENT_PROMPT | self.llm | StrOutputParser()
        return await chain.ainvoke({"text": data})
