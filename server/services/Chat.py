from typing import Any, cast

from fastapi.responses import StreamingResponse
from chathub.models import CerebrasChatRequestModel, CerebrasChatMessageModel
from chathub.workers import GetCerebrasApiKey
from chathub.enums import CerebrasChatMessageRoleEnum
import json
from server.models import ChatRequestModel
from server.implementations import ChatImpl
from dbhub import psqlDb
from server.workers import searchRagQuery
from raghub.models import (
    ConvertTextToEmbeddingResponseModel,
    RerankerResponseModel,
    RerankerItemModel,
    RerankeRequestModel,
)
import httpx

RetryLoopIndexLimit = 3


def getCerebrasChatService():
    from main import cerebrasChat

    return cerebrasChat


class Chat(ChatImpl):

    async def cerebrasContextChat(
        self, messages: list[CerebrasChatMessageModel]
    ) -> StreamingResponse | None:
        try:
            cerebrasChatResponse: Any = await getCerebrasChatService().Chat(
                modelParams=CerebrasChatRequestModel(
                    apiKey=GetCerebrasApiKey(),
                    model="gpt-oss-120b",
                    maxCompletionTokens=15000,
                    messages=messages,
                    stream=False,
                    temperature=0.2,
                    topP=1.0,
                )
            )
            return cerebrasChatResponse.content

        except Exception as _:
            return None

    async def cerebrasChat(
        self, messages: list[CerebrasChatMessageModel]
    ) -> StreamingResponse | None:
        try:
            cerebrasChatResponse: Any = await getCerebrasChatService().Chat(
                modelParams=CerebrasChatRequestModel(
                    apiKey=GetCerebrasApiKey(),
                    model="gpt-oss-120b",
                    maxCompletionTokens=90000,
                    messages=messages,
                    stream=True,
                    temperature=0.2,
                    topP=1.0,
                )
            )
            return cerebrasChatResponse

        except Exception as _:
            return None

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

    async def RerankeDocs(self, request: RerankeRequestModel) -> RerankerResponseModel:

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://34.92.4.0:8000/api/v1/ce/reranker",
                json={
                    "query": request.query,
                    "docs": request.docs,
                    "returnDocuments": request.returnDocuments,
                    "topN": request.topN,
                },
            )
            docs: list[RerankerItemModel] = []
            response = response.json()
            for doc in response["results"]:
                docs.append(
                    RerankerItemModel(
                        docIndex=doc["docIndex"],
                        doctext=doc["doctext"],
                        score=doc["score"],
                    )
                )

            return RerankerResponseModel(query=request.query, results=docs)

    async def HandleRagQuery(self, request: ChatRequestModel) -> StreamingResponse:
        queryVector = await self.ConvertTextToEmbeddings(texts=[request.query])
        docs: list[str] = []
        async with psqlDb.pool.acquire() as conn:
            await conn.set_type_codec(
                "jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
            )
            rows = await conn.fetch(
                searchRagQuery, cast(Any, queryVector)[0].embedding, 20
            )

            docs = [doc["text"] for doc in rows]

        topRerankedDocs = await self.RerankeDocs(
            request=RerankeRequestModel(
                query=request.query, returnDocuments=True, topN=10, docs=docs
            )
        )

        topDocs: list[str] = [cast(Any, doc.doctext) for doc in topRerankedDocs.results]

        systemInst = f"""
                        # Retrieved docs
                        {json.dumps(topDocs, indent=2)}

                        # Answering Guidelines
                        - Provide answers that are concise, clear, and directly relevant to the user’s query.
                        - Scale responses based on query type:
                        - **Short / fact-based (2–3 marks):** Answer in 2–3 sentences.
                        - **Explanation (10 marks):** Use structured detail with headings (###), bullet points, or numbered lists.

                        # Formatting Rules
                        - Use clean, professional **Markdown** (no raw HTML, no extra spacing issues).
                        - Always use headings (###) for sections in longer answers.
                        - Avoid unnecessary filler text. Keep tone professional and focused.
                        - Do **not** generate tables unless explicitly requested by the user.

                        # Images
                        - Include only images that are **highly relevant** to the user’s query.
                        - Present each image in this format:
                        ![Descriptive alt text](URL)
                        - Do not add decorative or unrelated images.
                        - Never embed images inside tables.

                        # Missing Information
                        - If no relevant information exists in the retrieved docs 
                        to answer the query, strict with this may be that is wrong query or some thing stick with this respond with:
                        "I'm sorry, but I couldn't find the information you're looking for in the provided documents. do you want me to try to answer based on  search?"
                        - Dont answer your own if the information is not available in the retrieved docs.
                        
                        """

        messages: list[CerebrasChatMessageModel] = [
            CerebrasChatMessageModel(
                role=CerebrasChatMessageRoleEnum.SYSTEM,
                content=systemInst,
            ),
            CerebrasChatMessageModel(
                role=CerebrasChatMessageRoleEnum.USER,
                content=cast(Any, request.query),
            ),
        ]

        contextResponse = await self.cerebrasContextChat(messages=messages)

        finalChatMessages: list[CerebrasChatMessageModel] = [
            CerebrasChatMessageModel(
                role=CerebrasChatMessageRoleEnum.SYSTEM,
                content=(
                    """You are a helpful AI assistant that helps people find information.
                    """
                ),
            )
        ]

        for message in request.messages:
            finalChatMessages.append(
                CerebrasChatMessageModel(
                    role=(
                        CerebrasChatMessageRoleEnum.USER
                        if message.role == "user"
                        else CerebrasChatMessageRoleEnum.ASSISTANT
                    ),
                    content=message.content,
                )
            )
        finalChatMessages.append(
            CerebrasChatMessageModel(
                role=CerebrasChatMessageRoleEnum.SYSTEM,
                content=(
                    f"For the current query: '{request.query}' ANSWER:\n{contextResponse}\n\n"
                ),
            )
        )
        finalChatMessages.append(
            CerebrasChatMessageModel(
                role=CerebrasChatMessageRoleEnum.USER,
                content=request.query,
            )
        )
        print(finalChatMessages)

        response = await self.cerebrasChat(messages=finalChatMessages)

        if response is not None:
            return response
        else:
            return StreamingResponse(
                iter([b"Sorry, Something went wrong !. Please Try again?"])
            )
