from raghub.implementations import BuildRagFromDocImpl
from raghub.workers import RagUtils, EXTRCT_INFO_FROM_CHUNK_FOR_GRAPH_RAG
import re
from chathub.models import CerebrasChatMessageModel, CerebrasChatRequestModel
from chathub.workers import GetCerebrasApiKey
from chathub.services import CerebrasChat
from typing import Any
import json
from chathub.enums import CerebrasChatMessageRoleEnum
from raghub.models import (
    ExtractRagInformationFromChunkResponseModel,
    GraphRagQuestionModel,
    GraphRagChunkTextsModel,
    ConvertTextToEmbeddingResponseModel,
    BuildRagResponseModel,
)
from raghub.enums import RagBuildProcessEnum
from uuid import uuid4
import httpx


cerebrasChat = CerebrasChat()


class BuildRagFromDoc(BuildRagFromDocImpl):

    def __init__(self):
        self.ragUtils = RagUtils()
        self.RetryLoopIndexLimit = 5

    async def HandleChunkProcessing(self, file: str) -> list[str]:
        chunks, images = self.ragUtils.ExtractChunksFromDoc(
            file=file, chunkOLSize=100, chunkSize=1200
        )
        processedChunk: list[str] = []

        for chunk in chunks:

            matchedIndex = re.findall(r"<<[Ii][Mm][Aa][Gg][Ee]-([0-9]+)>>", chunk)
            indeces = list(map(int, matchedIndex))
            if len(indeces) == 0:
                processedChunk.append(chunk)
            else:
                chunkText = chunk
                for index in indeces:
                    imageUrl = await self.ragUtils.UploadImageToFirebase(
                        base64Str=images[index - 1],
                        folder="opd",
                    )
                    token = f"<<image-{index}>>"
                    chunkText = chunkText.replace(token, f"![Image]({imageUrl})")
                processedChunk.append(chunkText)

        return processedChunk

    async def ExtractRagInformationFromChunk(
        self,
        messages: list[CerebrasChatMessageModel],
        retryLoopIndex: int,
    ) -> ExtractRagInformationFromChunkResponseModel:
        if retryLoopIndex > self.RetryLoopIndexLimit:
            raise Exception(
                "Exception while extarcting  questions from chunk"
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
                        "questions": {"type": "array", "items": {"type": "string"}},
                        "chunk": {"type": "string"},
                    },
                    "required": [ "chunk", "questions"],
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

    async def HandleRagBuildProcess(
        self, file: str, process: RagBuildProcessEnum
    ) -> BuildRagResponseModel | None:

        if process == RagBuildProcessEnum.GRAPHRAG:
            chunks = await self.HandleChunkProcessing(file=file)
            chunkTexts: list[GraphRagChunkTextsModel] = []
            chunkQuestions: list[GraphRagQuestionModel] = []

            for chunk in chunks:
                messages: list[CerebrasChatMessageModel] = [
                    CerebrasChatMessageModel(
                        role=CerebrasChatMessageRoleEnum.SYSTEM,
                        content=EXTRCT_INFO_FROM_CHUNK_FOR_GRAPH_RAG,
                    ),
                    CerebrasChatMessageModel(
                        role=CerebrasChatMessageRoleEnum.USER, content=chunk
                    ),
                ]
                import time

                time.sleep(1)
                chunkGraphRagInfo = await self.ExtractRagInformationFromChunk(
                    messages=messages, retryLoopIndex=0
                )
                chunkId = uuid4()
                thisChunkText = GraphRagChunkTextsModel(
                    id=chunkId, text=chunkGraphRagInfo.chunk
                )
                thisChunkQuestions = [
                    GraphRagQuestionModel(id=uuid4(), chunkId=chunkId, text=rel)
                    for rel in chunkGraphRagInfo.questions
                ]

                texts: list[str] = []
                texts.append(chunkGraphRagInfo.chunk)
                for _, claim in enumerate(chunkGraphRagInfo.questions):
                    texts.append(claim)

                textVectors = await self.ConvertTextToEmbeddings(texts=texts)
                c = 1
                cLen = len(chunkGraphRagInfo.questions)
                if textVectors is not None:
                    thisChunkText.embedding = textVectors[0].embedding
                    for cIndex, item in enumerate(textVectors[c : c + cLen]):
                        thisChunkQuestions[cIndex].embedding = item.embedding

                chunkTexts.append(thisChunkText)
                chunkQuestions.extend(thisChunkQuestions)
            return BuildRagResponseModel(
                chunkQuestions=chunkQuestions,
                chunks=chunkTexts,
            )

        else:
            return None
