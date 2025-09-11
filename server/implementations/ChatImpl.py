from abc import ABC, abstractmethod
from chathub.models import CerebrasChatMessageModel
from fastapi.responses import StreamingResponse
from server.models import ChatRequestModel, PreProcessUserQueryResponseModel
from raghub.models import (
    ConvertTextToEmbeddingResponseModel,
    RerankeRequestModel,
    RerankerResponseModel,
)


class ChatImpl(ABC):
    @abstractmethod
    async def CerebrasNormalChat(
        self, messages: list[CerebrasChatMessageModel]
    ) -> StreamingResponse | None:
        pass

    @abstractmethod
    async def PreProcessUserQuery(
        self, query: str, messages: list[CerebrasChatMessageModel], loopIndex: int
    ) -> PreProcessUserQueryResponseModel:
        pass

    @abstractmethod
    async def CerebrasHmisAnswer(
        self, messages: list[CerebrasChatMessageModel]
    ) -> StreamingResponse | None:
        pass

    @abstractmethod
    async def ConvertTextToEmbeddings(
        self, texts: list[str]
    ) -> list[ConvertTextToEmbeddingResponseModel] | None:
        pass

    @abstractmethod
    async def RerankeDocs(
        self, request: RerankeRequestModel
    ) -> RerankerResponseModel | None:
        pass

    @abstractmethod
    async def HandleRagQuery(self, request: ChatRequestModel) -> StreamingResponse:
        pass
