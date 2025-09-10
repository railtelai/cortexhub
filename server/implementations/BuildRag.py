from abc import ABC, abstractmethod
from typing import Any


class BuildRagImpl(ABC):

    @abstractmethod
    async def BuildRag(self, file: str, db: Any):
        pass

    @abstractmethod
    async def BuildYtRag(self, videoId: str, db: Any):
        pass

    @abstractmethod
    async def BuildQaRag(self, file: str, db: Any):
        pass
