from pydantic import BaseModel



class ChatRequestModel(BaseModel):
    query:str