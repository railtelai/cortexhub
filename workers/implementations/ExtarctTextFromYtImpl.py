from abc import ABC, abstractmethod
from workers.models import ExtractTextFromYtResponseModel


class ExtractTextFromYtImpl(ABC):

    @abstractmethod
    def ExtractText(
        self, videoId: str, chunkSec: int = 30
    ) -> list[ExtractTextFromYtResponseModel]:
        pass
