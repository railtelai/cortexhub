from pydantic import BaseModel


class ExtractTextFromYtResponseModel(BaseModel):
    videoId: str
    chunkText: str
    chunkUrl: str
