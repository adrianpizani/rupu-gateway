from abc import ABC, abstractmethod

class BaseProvider(ABC):
    @abstractmethod
    async def process(self, data: str):
        pass
