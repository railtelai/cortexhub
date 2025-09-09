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
from raghub.models import ConvertTextToEmbeddingResponseModel,RerankerResponseModel,RerankerItemModel,RerankeRequestModel
import httpx

RetryLoopIndexLimit = 3


def getCerebrasChatService():
    from main import cerebrasChat

    return cerebrasChat



class Chat(ChatImpl):

    async def cerebrasChat(
        self, messages: list[CerebrasChatMessageModel]
    ) -> StreamingResponse | None:
        try:
            cerebrasChatResponse: Any = await getCerebrasChatService().Chat(
                modelParams=CerebrasChatRequestModel(
                    apiKey=GetCerebrasApiKey(),
                    model="gpt-oss-120b",
                    maxCompletionTokens=5000,
                    messages=messages,
                    stream=True,
                    temperature=0.7,
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
    
    async def RerankeDocs(
        self, request:RerankeRequestModel
    ) -> RerankerResponseModel :

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://34.92.4.0:8000/api/v1/ce/reranker", json={

                    "query": request.query,
                    "docs":request.docs ,
                    "returnDocuments":request.returnDocuments,
                    "topN":request.topN
                }
            )
            docs:list[RerankerItemModel] = []
            response = response.json()
            for doc in response["results"]:
                docs.append(
                    RerankerItemModel(
                        docIndex=doc["docIndex"],
                        doctext=doc["doctext"],
                        score=doc["score"]
                    )
                )

            return RerankerResponseModel(
                query=request.query,
                results=docs
            )

    

    async def HandleRagQuery(self, request: ChatRequestModel) -> StreamingResponse:
        queryVector = await self.ConvertTextToEmbeddings(
            texts=[
                request.query
            ]
        )
        docs:list[str] = []
        async with psqlDb.pool.acquire() as conn:
            await conn.set_type_codec(
                "jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
            )
            rows = await conn.fetch(searchRagQuery, cast(Any,queryVector)[0].embedding, 50)

            docs = [doc["text"] for doc in rows]
            

        topRerankedDocs = await self.RerankeDocs(
            request=RerankeRequestModel(
                query=request.query,
                returnDocuments=True,
                topN=7,
                docs=docs
            )
        )
        print(topRerankedDocs)

        topDocs: list[str] = [cast(Any,doc.doctext) for doc in topRerankedDocs.results]

        systemInst = f"""
                # Retrieved docs
                {json.dumps(topDocs, indent=2)}

                # Instructions
                - Write answers concisely and proportional to the query:
                - Short/fact-based (2–3 marks): answer in 2–3 sentences.
                - Explanation (10 marks): answer in clear, structured detail (use headings, bullet points, or numbered lists).
                - Formatting rules:
                - Use clean **Markdown** only (no tables unless explicitly requested).
                - Always use headings (###) for clarity in longer answers.
                - Keep answers professional, without unnecessary filler text.
                - Images:
                - include only ** most relevant images** to user query.
                - Show each image as:
                    ![alt text](URL)
                - If the image is too large or detailed, use:
                    <img src="URL" width="600"/>
                - Never embed images inside tables.
                - If no relevant info exists in the retrieved docs, reply with exactly:
                "We don’t have information about this. Please contact the helpdesk for further assistance."
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

        response = await self.cerebrasChat(messages=messages)
        if response is not None:
            return response
        else:
            return StreamingResponse(
                iter([b"Sorry, Something went wrong !. Please Try again?"])
            )
