from pydantic import BaseModel
from uuid import UUID
from raghub.models import GraphRagQuestionModel,GraphRagChunkTextsModel



class ExtarctQaResponseModel(BaseModel):
    questions: list[str]
    answers: list[str]


class HandleBuildQaRagProcessResponseModel(BaseModel):
    chunks:list[GraphRagChunkTextsModel]
    questions: list[GraphRagQuestionModel]
