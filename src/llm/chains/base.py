"""Base abstracta para todas las LangChain Chains del pipeline.

Cada chain recibe un LLM en el constructor y define su propio
prompt + pipeline. La interfaz común es `async process(data) -> str`,
que es la misma que usan los providers mock actuales, permitiendo
intercambiarlos sin tocar el resto del sistema.
"""
from abc import ABC, abstractmethod
from langchain_core.language_models import BaseLanguageModel


class BaseLLMChain(ABC):
    """Chain base que usa un LLM para procesar datos textuales.

    Cada subclase debe implementar `process()` y definir su propio
    prompt template y pipeline de LangChain.

    Uso:
        class MiChain(BaseLLMChain):
            async def process(self, data: str) -> str:
                chain = MI_PROMPT | self.llm | StrOutputParser()
                return await chain.ainvoke({"text": data})
    """

    def __init__(self, llm: BaseLanguageModel):
        self.llm = llm

    @abstractmethod
    async def process(self, data: str) -> str:
        """Procesa el texto de entrada y retorna el resultado.
        
        Args:
            data: Texto a procesar.
        
        Returns:
            Resultado del procesamiento (generalmente JSON en string).
        """
        ...
