import asyncio
from providers.base import BaseProvider

class ExtractorProvider(BaseProvider):
    async def process(self, data: str)->str:
        pass

class FastExtractorProvider(ExtractorProvider):
    async def process(self, data: str)->str:
        await asyncio.sleep(0.1)
        return f"FAST EXTRACTED {data[:20]}"
    
class SlowExtractorProvider(ExtractorProvider):
    async def process(self, data: str)->str:
        await asyncio.sleep(2.0)
        return f"SLOW EXTRACTED {data[:20]}"

def get_extractor(type_name: str) -> ExtractorProvider:
    if type_name == 'fast':
        return FastExtractorProvider()
    if type_name == 'slow':
        return SlowExtractorProvider()
    if type_name == 'default':
        return FastExtractorProvider()
    raise ValueError(f'Type {type_name} extractor not supported')



