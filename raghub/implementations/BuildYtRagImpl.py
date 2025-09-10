from abc import ABC, abstractmethod
from raghub.models import (
    ExtractRagInformationFromChunkResponseModel,
    ConvertTextToEmbeddingResponseModel,
    BuildRagResponseModel,
)
from chathub.models import CerebrasChatMessageModel


class BuildYtRagImpl(ABC):

    @abstractmethod
    async def ExtractRagInformationFromChunk(
        self, messages: list[CerebrasChatMessageModel], retryLoopIndex: int
    ) -> ExtractRagInformationFromChunkResponseModel:
        pass

    @abstractmethod
    async def ConvertTextToEmbeddings(
        self, texts: list[str]
    ) -> list[ConvertTextToEmbeddingResponseModel] | None:
        pass

    @abstractmethod
    async def HandleRagBuildProcess(
        self, videoId: str
    ) -> BuildRagResponseModel | None:
        pass
