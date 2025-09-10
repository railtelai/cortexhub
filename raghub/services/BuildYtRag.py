from raghub.implementations import BuildYtRagImpl
from raghub.workers import RagUtils, EXTRCT_INFO_FROM_CHUNK_YT_VIDEO
from chathub.models import CerebrasChatMessageModel, CerebrasChatRequestModel
from chathub.workers import GetCerebrasApiKey
from chathub.services import CerebrasChat
from typing import Any
import json
from chathub.enums import CerebrasChatMessageRoleEnum
from raghub.models import (
    ExtractRagInformationFromChunkResponseModel,
    GraphRagQuestionModel,
    GraphRagRelationModel,
    GraphRagChunkTextsModel,
    ConvertTextToEmbeddingResponseModel,
    BuildRagResponseModel,
)
from uuid import uuid4
import httpx    


cerebrasChat = CerebrasChat()


class BuildYtRag(BuildYtRagImpl):

    def __init__(self):
        self.ragUtils = RagUtils()
        self.RetryLoopIndexLimit = 5

    async def ExtractRagInformationFromChunk(
        self,
        messages: list[CerebrasChatMessageModel],
        retryLoopIndex: int,
    ) -> ExtractRagInformationFromChunkResponseModel:
        if retryLoopIndex > self.RetryLoopIndexLimit:
            raise Exception(
                "Exception while extarcting relation and questions from chunk"
            )

        cerebrasChatResponse: Any = await cerebrasChat.Chat(
            modelParams=CerebrasChatRequestModel(
                apiKey=GetCerebrasApiKey(),
                model="qwen-3-235b-a22b-instruct-2507",
                maxCompletionTokens=30000,
                messages=messages,
                temperature=0.2,
                responseFormat={
                    "type": "object",
                    "properties": {
                        "relations": {"type": "array", "items": {"type": "string"}},
                        "questions": {"type": "array", "items": {"type": "string"}},
                        "chunk": {"type": "string"},
                    },
                    "required": ["relations", "chunk", "questions"],
                    "additionalProperties": False,
                },
            )
        )
        chatResponse: Any = {}
        try:

            chatResponse = json.loads(cerebrasChatResponse.content).get("response")

        except Exception as e:
            print("Error occured while extracting realtions from chunk retrying ...")
            print(e)
            messages.append(
                CerebrasChatMessageModel(
                    role=CerebrasChatMessageRoleEnum.USER,
                    content="Please generate a valid json object",
                )
            )

            await self.ExtractRagInformationFromChunk(
                messages=messages,
                retryLoopIndex=retryLoopIndex + 1,
            )

        response = ExtractRagInformationFromChunkResponseModel(
            chunk=chatResponse.get("chunk"),
            questions=chatResponse.get("questions"),
            relations=chatResponse.get("relations"),
        )
        return response

    async def ConvertTextToEmbeddings(
        self, texts: list[str]
    ) -> list[ConvertTextToEmbeddingResponseModel] | None:

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://34.92.4.0:8000/api/v1/embedding", json={"texts": texts}
            )
            response = response.json()
            embeddings: list[ConvertTextToEmbeddingResponseModel] = []
            for item in response["embeddings"]:
                embeddings.append(
                    ConvertTextToEmbeddingResponseModel(
                        index=item["index"], embedding=item["embedding"]
                    )
                )
            return embeddings

        return None

    async def HandleRagBuildProcess(self, videoId: str) -> BuildRagResponseModel | None:
        chunks = self.ragUtils.ExtractChunksFromYtVideo(chunkSec=200, videoId=videoId)

        chunkTexts: list[GraphRagChunkTextsModel] = []
        chunkRelations: list[GraphRagRelationModel] = []
        chunkQuestions: list[GraphRagQuestionModel] = []

        for chunk in chunks:
            messages: list[CerebrasChatMessageModel] = [
                CerebrasChatMessageModel(
                    role=CerebrasChatMessageRoleEnum.SYSTEM,
                    content=EXTRCT_INFO_FROM_CHUNK_YT_VIDEO,
                ),
                CerebrasChatMessageModel(
                    role=CerebrasChatMessageRoleEnum.USER,
                    content=chunk,
                ),
            ]

            chunkGraphRagInfo = await self.ExtractRagInformationFromChunk(
                messages=messages, retryLoopIndex=0
            )

            chunkId = uuid4()

            thisChunkText = GraphRagChunkTextsModel(
                id=chunkId, text=chunkGraphRagInfo.chunk
            )

            thisChunkRelations = [
                GraphRagRelationModel(id=uuid4(), chunkId=chunkId, text=rel)
                for rel in chunkGraphRagInfo.relations
            ]

            thisChunkQuestions = [
                GraphRagQuestionModel(id=uuid4(), chunkId=chunkId, text=question)
                for question in chunkGraphRagInfo.questions
            ]

            texts: list[str] = [chunkGraphRagInfo.chunk]
            texts.extend(chunkGraphRagInfo.questions)
            texts.extend(chunkGraphRagInfo.relations)

            textVectors = await self.ConvertTextToEmbeddings(texts=texts)

            if textVectors is not None:
                thisChunkText.embedding = textVectors[0].embedding

                qLen = len(chunkGraphRagInfo.questions)
                for i, item in enumerate(textVectors[1 : 1 + qLen]):
                    thisChunkQuestions[i].embedding = item.embedding

                for i, item in enumerate(textVectors[1 + qLen :]):
                    thisChunkRelations[i].embedding = item.embedding

            chunkTexts.append(thisChunkText)
            chunkRelations.extend(thisChunkRelations)
            chunkQuestions.extend(thisChunkQuestions)

        return BuildRagResponseModel(
            chunkQuestions=chunkQuestions,
            chunkRelations=chunkRelations,
            chunks=chunkTexts,
        )
