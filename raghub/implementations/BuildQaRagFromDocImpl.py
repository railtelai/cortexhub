from abc import ABC, abstractmethod
from raghub.models import  ExtarctQaResponseModel, HandleBuildQaRagProcessResponseModel
from raghub.models import ConvertTextToEmbeddingResponseModel


class BuildQaRagFromDocImpl(ABC):

    @abstractmethod
    def ExtarctQaFromText(self, text: str) -> ExtarctQaResponseModel:
        pass

    @abstractmethod
    async def ConvertTextToEmbeddings(
        self, texts: list[str]
    ) -> list[ConvertTextToEmbeddingResponseModel] | None:
        pass

    @abstractmethod
    async def HandleBuildQaRagProcess(self, file: str) -> HandleBuildQaRagProcessResponseModel:
        pass
