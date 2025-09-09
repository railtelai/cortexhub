from abc import ABC, abstractmethod
from raghub.models import (
    ExtractGraphRagInformationFromChunkResponseModel,
    ConvertTextToEmbeddingResponseModel,
    BuildGraphRagResponseModel,
)
from chathub.models import CerebrasChatMessageModel
from raghub.enums import RagBuildProcessEnum


class BuildRagFromDocImpl(ABC):

    @abstractmethod
    async def HandleChunkProcessing(self, file: str) -> list[str]:
        pass

    @abstractmethod
    async def ExtractGraphRagInformationFromChunk(
        self, messages: list[CerebrasChatMessageModel], retryLoopIndex: int
    ) -> ExtractGraphRagInformationFromChunkResponseModel:
        pass

    @abstractmethod
    async def ConvertTextToEmbeddings(
        self, texts: list[str]
    ) -> list[ConvertTextToEmbeddingResponseModel] | None:
        pass

    @abstractmethod
    async def HandleRagBuildProcess(
        self, file: str, process: RagBuildProcessEnum
    ) -> BuildGraphRagResponseModel | None:
        pass
