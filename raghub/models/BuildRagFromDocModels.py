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
    chunks:list[GraphRagChunkTextsModel]
    chunkQuestions:list[GraphRagQuestionModel]
    chunkRelations:list[GraphRagRelationModel]
