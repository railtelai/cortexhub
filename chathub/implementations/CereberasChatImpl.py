from abc import ABC, abstractmethod

from fastapi.responses import StreamingResponse

from chathub.models import CerebrasChatRequestModel, CerebrasChatResponseModel


class CerebrasChatImpl(ABC):

    @abstractmethod
    async def Chat(
        self, modelParams: CerebrasChatRequestModel
    ) -> CerebrasChatResponseModel | StreamingResponse:
        pass

    @abstractmethod
    def HandleApiStatusError(self, statusCode: int) -> CerebrasChatResponseModel:
        pass
