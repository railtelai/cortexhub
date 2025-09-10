from abc import ABC, abstractmethod
from chathub.models import CerebrasChatMessageModel
from fastapi.responses import StreamingResponse
from server.models import ChatRequestModel
from raghub.models import (
    ConvertTextToEmbeddingResponseModel,
    RerankeRequestModel,
    RerankerResponseModel,
)


class ChatImpl(ABC):
    @abstractmethod
    async def cerebrasContextChat(
        self, messages: list[CerebrasChatMessageModel]
    ) -> StreamingResponse | None:
        pass

    @abstractmethod
    async def cerebrasChat(
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
