"""
Chain de extracción de información estructurada usando un LLM.

Toma texto no estructurado y extrae: tema principal, entidades,
fechas y resumen. Retorna JSON.
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.llm.chains.base import BaseLLMChain
from src.llm.chains.registry import ChainRegistry


EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Eres un extractor de información experto. "
               "Del texto proporcionado, extrae:\n"
               "1. Tema principal\n"
               "2. Entidades (personas, lugares, organizaciones)\n"
               "3. Fechas mencionadas\n"
               "4. Resumen de una oración\n\n"
               "Responde ÚNICAMENTE con un objeto JSON válido, sin explicaciones."),
    ("human", "{text}"),
])


@ChainRegistry.register("extract")
class ExtractionChain(BaseLLMChain):
    """Chain que extrae información estructurada de un texto usando un LLM."""

    async def process(self, data: str) -> str:
        chain = EXTRACTION_PROMPT | self.llm | StrOutputParser()
        return await chain.ainvoke({"text": data})
