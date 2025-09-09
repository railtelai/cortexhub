from abc import ABC, abstractmethod
from typing import List, Tuple


class ExtractTextFromDocImpl(ABC):

    @abstractmethod
    def ExtractTextFromXlsx(self, docPath: str) -> str:
        pass

    @abstractmethod
    def ExtractTextFromCsv(self, docPath: str) -> str:
        pass

    @abstractmethod
    def ExtractTextAndImagesFromPdf(self, docPath: str) -> Tuple[str, List[str]]:
        pass

    @abstractmethod
    def ExtractTextFromDoc(self, docPath: str) -> Tuple[str, List[str]]:
        pass