from abc import ABC, abstractmethod
from typing import Tuple


class RagUtilsImpl(ABC):

    @abstractmethod
    def ExtractChunksFromDoc(
        self, file: str, chunkSize: int, chunkOLSize: int | None = 0
    ) -> Tuple[list[str], list[str]]:
        pass

    @abstractmethod
    async def UploadImageToFirebase(self, base64Str: str, folder: str) -> str:
        pass

    @abstractmethod
    def ExtractChunksFromYtVideo(
        self, videoId: str, chunkSec: int = 100
    ) -> list[str]:
        pass
