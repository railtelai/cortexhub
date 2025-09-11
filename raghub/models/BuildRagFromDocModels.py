from pydantic import BaseModel
from uuid import UUID


class ExtractRagInformationFromChunkResponseModel(BaseModel):
    chunk: str
    questions: list[str]


class GraphRagChunkTextsModel(BaseModel):
    id: UUID
    text: str
    embedding: list[float] | None = None


class GraphRagQuestionModel(BaseModel):
    id: UUID
    chunkId: UUID
    text: str
    embedding: list[float] | None = None




class ConvertTextToEmbeddingResponseModel(BaseModel):
    index: int
    embedding: list[float]


class BuildRagResponseModel(BaseModel):
    chunks: list[GraphRagChunkTextsModel]
    chunkQuestions: list[GraphRagQuestionModel]


class RerankeRequestModel(BaseModel):
    query: str
    docs: list[str]
    returnDocuments: bool = False
    topN: int = 10


class RerankerItemModel(BaseModel):
    docIndex: int
    doctext: str | None = None
    score: float


class RerankerResponseModel(BaseModel):
    results: list[RerankerItemModel]
    query: str
