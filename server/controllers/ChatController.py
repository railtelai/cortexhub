from fastapi import APIRouter
from server.models import ChatRequestModel
from server.services import Chat


ChatRouter = APIRouter()
ChatService = Chat()


@ChatRouter.post("/chat/public")
async def HandlePublicChat(request: ChatRequestModel):
    response = await ChatService.HandleRagQuery(request=request)
    return response
