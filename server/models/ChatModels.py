from pydantic import BaseModel


class ChatMessageModel(BaseModel):
    role: str
    content: str


class ChatRequestModel(BaseModel):
    query: str
    messages: list[ChatMessageModel] = []
