from fastapi import APIRouter
from dbhub import PsqlDb
from server.services import BuildRag

ragRouter = APIRouter()
buildRagService = BuildRag()


async def GetDb() -> PsqlDb:

    from main import psqlDb

    return psqlDb


# @ragRouter.get("/brfd")
# async def BuildFromDoc():
#     return await buildRagService.BuildRag("./others/opd_manual.pdf", await GetDb())


# @ragRouter.get("/brfd")
# async def BuildFromDoc():
#     return await buildRagService.BuildQaRag("./others/faq.csv", await GetDb())


@ragRouter.get("/brfd")
async def BuildFromDoc(video_id: str):
    db = await GetDb()
    return await buildRagService.BuildYtRag(video_id, db)
