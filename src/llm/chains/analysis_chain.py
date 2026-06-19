"""
Chain de análisis de texto usando un LLM.

Toma texto y analiza: sentimiento, categorías, tono y palabras clave.
Retorna JSON.
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.llm.chains.base import BaseLLMChain
from src.llm.chains.registry import ChainRegistry


ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Eres un analista de texto experto. "
               "Del texto proporcionado, identifica:\n"
               "1. Sentimiento general (positivo, negativo, neutral)\n"
               "2. Categorías/tópicos principales\n"
               "3. Tono del texto (formal, informal, técnico, humorístico, etc.)\n"
               "4. Palabras clave (hasta 5)\n\n"
               "Responde ÚNICAMENTE con un objeto JSON válido, sin explicaciones."),
    ("human", "{text}"),
])


@ChainRegistry.register("analyze")
class AnalysisChain(BaseLLMChain):
    """Chain que analiza sentimiento, categorías y tono de un texto."""

    async def process(self, data: str) -> str:
        chain = ANALYSIS_PROMPT | self.llm | StrOutputParser()
        return await chain.ainvoke({"text": data})
