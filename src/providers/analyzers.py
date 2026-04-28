import asyncio
from providers.base import BaseProvider

class AnalyzerProvider(BaseProvider):
    async def process(self, data: str)->str:
        await asyncio.sleep(0.5)
        return f"ANALYZED {data[:20]}"

def get_analyzer(type_name: str) -> AnalyzerProvider:
    return AnalyzerProvider()