from pydantic import BaseModel
from uuid import UUID


class ExtractGraphRagInformationFromChunkResponseModel(BaseModel):
    chunk: str
    relations: list[str]
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


class GraphRagRelationModel(BaseModel):
    id: UUID
    chunkId: UUID
    text: str
    embedding: list[float] | None = None


class ConvertTextToEmbeddingResponseModel(BaseModel):
    index: int
    embedding: list[float]


class BuildGraphRagResponseModel(BaseModel):
    chunks: list[GraphRagChunkTextsModel]
    chunkQuestions: list[GraphRagQuestionModel]
    chunkRelations: list[GraphRagRelationModel]


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
