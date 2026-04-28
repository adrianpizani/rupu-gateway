import asyncio
from providers.base import BaseProvider

class EnricherProvider(BaseProvider):
    async def process(self, data: str)->str:
        await asyncio.sleep(0.6)
        return f"ENRICHED {data[:20]}"
    
def get_enricher(type_name: str) -> EnricherProvider:
    return EnricherProvider()
