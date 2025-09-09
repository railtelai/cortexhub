from typing import Any, List, Optional
from pydantic import BaseModel

from chathub.enums import (
    CerebrasChatMessageRoleEnum,
    CerebrasChatResponseStatusEnum,
)


class CerebrasChatMessageModel(BaseModel):
    role: Optional[CerebrasChatMessageRoleEnum] = CerebrasChatMessageRoleEnum.USER
    content: str


class CerebrasChatRequestModel(BaseModel):
    model: str = "gpt-oss-120b"
    messages: List[CerebrasChatMessageModel]
    maxCompletionTokens: Optional[int] = 3000
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.2
    apiKey: str
    responseFormat: Optional[Any] = None
    topP: float = 0.9
    seed: int = 42


class CerebrasChatChoiceMessageModel(BaseModel):
    role: CerebrasChatMessageRoleEnum = CerebrasChatMessageRoleEnum.ASSISTANT
    content: str


class CerebrasChatChoiceModel(BaseModel):
    index: int = 0
    message: CerebrasChatChoiceMessageModel


class CerebrasChatUsageModel(BaseModel):
    promptTokens: int | None = None
    completionTokens: int | None = None
    totalTokens: int | None = None


class CerebrasChatDataModel(BaseModel):
    id: str
    choices: List[CerebrasChatChoiceModel] = []
    created: int
    model: str = "llama-3.3-70b"
    totalTime: float = 0.0
    usage: CerebrasChatUsageModel


class CerebrasChatResponseModel(BaseModel):
    status: CerebrasChatResponseStatusEnum = CerebrasChatResponseStatusEnum.SUCCESS
    content: str | None = None
