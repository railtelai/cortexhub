from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from chathub.services import CerebrasChat
from server.controllers import ragRouter,ChatRouter
import asyncio

from dbhub import psqlDb

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(psqlDb.connect())
    yield
    try:
        await asyncio.wait_for(psqlDb.close(), timeout=3)
    except asyncio.TimeoutError:
        print("⚠️ DB close timed out")


server = FastAPI(lifespan=lifespan)

server.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
server.include_router(ragRouter, prefix="/api/v1/build")
server.include_router(ChatRouter, prefix="/api/v1/ask")
cerebrasChat = CerebrasChat()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:server", host="0.0.0.0", port=8001, reload=True)
