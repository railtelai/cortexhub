from typing import Any, cast

from fastapi.responses import StreamingResponse
from chathub.models import CerebrasChatRequestModel, CerebrasChatMessageModel
from chathub.workers import GetCerebrasApiKey
from chathub.enums import CerebrasChatMessageRoleEnum
import json
from server.models import ChatRequestModel, PreProcessUserQueryResponseModel
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
    def __init__(self):
        self.RetryLoopIndexLimit = 5

    async def PreProcessUserQuery(
        self, query: str, messages: list[CerebrasChatMessageModel], loopIndex: int
    ) -> PreProcessUserQueryResponseModel:

        if loopIndex > self.RetryLoopIndexLimit:
            raise Exception(
                "Exception while extarcting relation and questions from chunk"
            )

        preProcessResponse: Any = await getCerebrasChatService().Chat(
            modelParams=CerebrasChatRequestModel(
                apiKey=GetCerebrasApiKey(),
                model="llama-4-scout-17b-16e-instruct",
                maxCompletionTokens=2000,
                messages=messages,
                temperature=0.1,
                topP=0.9,
                responseFormat={
                    "type": "object",
                    "properties": {
                        "cleanquery": {"type": "string"},
                        "type": {
                            "type": "string",
                            "enum": [
                                "PREVIOUS",
                                "ABUSE_LANG_ERROR",
                                "CONTACT_INFO_ERROR",
                                "HMIS",
                            ],
                        },
                    },
                    "required": ["type"],
                    "additionalProperties": False,
                },
            )
        )

        chatResponse: Any = {}
        try:

            chatResponse = json.loads(preProcessResponse.content).get("response")

        except Exception as e:
            print("Error occured while extracting realtions from chunk retrying ...")
            print(e)
            messages.append(
                CerebrasChatMessageModel(
                    role=CerebrasChatMessageRoleEnum.USER,
                    content="Please generate a valid json object",
                )
            )
            await self.PreProcessUserQuery(
                messages=messages,
                loopIndex=loopIndex + 1,
                query=query,
            )
        return PreProcessUserQueryResponseModel(
            cleanQuery=chatResponse.get("cleanquery"),
            type=chatResponse.get("type"),
        )

    async def CerebrasNormalChat(
        self, messages: list[CerebrasChatMessageModel]
    ) -> StreamingResponse | None:
        try:
            cerebrasChatResponse: Any = await getCerebrasChatService().Chat(
                modelParams=CerebrasChatRequestModel(
                    apiKey=GetCerebrasApiKey(),
                    model="qwen-3-235b-a22b-instruct-2507",
                    maxCompletionTokens=15000,
                    messages=messages,
                    stream=True,
                    temperature=0.3,
                    topP=0.9,
                )
            )
            return cerebrasChatResponse

        except Exception as _:
            return None

    async def CerebrasHmisAnswer(
        self, messages: list[CerebrasChatMessageModel]
    ) -> StreamingResponse | None:
        try:
            cerebrasChatResponse: Any = await getCerebrasChatService().Chat(
                modelParams=CerebrasChatRequestModel(
                    apiKey=GetCerebrasApiKey(),
                    model="gpt-oss-120b",
                    maxCompletionTokens=10000,
                    messages=messages,
                    stream=True,
                    temperature=0.2,
                    topP=0.9,
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

        preProcessMessage: list[CerebrasChatMessageModel] = [
            CerebrasChatMessageModel(
                role=CerebrasChatMessageRoleEnum.SYSTEM,
                content="""
                You are a strict query pre-processor. Always return a JSON object only with two fields:
                {
                "cleanquery": "<string>",
                "type": "<enum>"
                }

                Classification rules for "type":
                - "CONTACT_INFO_ERROR": If the user shares  personal, confidential, or sensitive information (phone, email, address, account details, medical record number, ID numbers, etc.).
                - "ABUSE_LANG_ERROR": If the current user message only  contains abusive, offensive, hateful, violent, harassing, or threatening language dont take previous messages abusive messages focus on current one.
                - "HMIS": If the user query is about OPD, HMIS, hospital records, patient registration, OPD workflow, prescriptions, reports, or anything related to the healthcare management information system (HMIS). HMIS is a digital platform used in hospitals and health facilities to manage OPD, patient data, treatment records, prescriptions, lab reports, billing, and overall healthcare workflows. Questions like “what is OPD”, “what is HMIS”, or “explain OPD process” fall here.
                - "PREVIOUS": If and only if the user explicitly refers to their previous query, previous question, or previous message (e.g., “same as before”, “what about the last one”, “yes to the previous”, “continue from earlier”).

                Rules for "cleanquery":
                - Always normalize the query into clean English.
                - If user asks in Hindi or another non-English language → translate to English.
                - Fix spelling mistakes and grammar errors.
                - Form the user query into a meaningful question if it is not already in question form.

                Constraints:
                - Output must be valid JSON only (no markdown, no commentary).
                - Keys must be exactly "cleanquery" and "type".
                - "type" must be one of: "PREVIOUS", "ABUSE_LANG_ERROR", "CONTACT_INFO_ERROR", "HMIS". """,
            ),
        ]
        for message in request.messages:
            preProcessMessage.append(
                CerebrasChatMessageModel(
                    content=message.content,
                    role=(
                        CerebrasChatMessageRoleEnum.USER
                        if message.role == "user"
                        else CerebrasChatMessageRoleEnum.SYSTEM
                    ),
                )
            )
        preProcessMessage.append(
            CerebrasChatMessageModel(
                role=CerebrasChatMessageRoleEnum.USER,
                content=cast(Any, request.query),
            ),
        )

        preProcessResponse = await self.PreProcessUserQuery(
            query=request.query, loopIndex=0, messages=preProcessMessage
        )
        print(preProcessResponse.type)

        if preProcessResponse.type == "ABUSE_LANG_ERROR":

            async def abuseStream():
                yield "data: Sorry, your query contains abusive language.\n\n"

            return StreamingResponse(abuseStream(), media_type="text/event-stream")

        elif preProcessResponse.type == "CONTACT_INFO_ERROR":

            async def contactInfo():
                yield "data: Sorry, your query contains personal or confidential information.\n\n"

            return StreamingResponse(contactInfo(), media_type="text/event-stream")

        elif preProcessResponse.type == "PREVIOUS":
            generalMessages: list[CerebrasChatMessageModel] = [
                CerebrasChatMessageModel(
                    role=CerebrasChatMessageRoleEnum.SYSTEM,
                    content="systemInst",
                )
            ]

            for message in request.messages:
                generalMessages.append(
                    CerebrasChatMessageModel(
                        content=message.content,
                        role=(
                            CerebrasChatMessageRoleEnum.USER
                            if message.role == "user"
                            else CerebrasChatMessageRoleEnum.SYSTEM
                        ),
                    )
                )
            generalMessages.append(
                CerebrasChatMessageModel(
                    content=preProcessResponse.cleanQuery,
                    role=(CerebrasChatMessageRoleEnum.USER),
                )
            )
            response = await self.CerebrasNormalChat(messages=generalMessages)

            if response is not None:
                return response
            else:

                async def contactInfoStream():
                    yield "data: Sorry, Something went wrong !. Please Try again?\n\n"

                return StreamingResponse(
                    contactInfoStream(), media_type="text/event-stream"
                )

        else:
            queryVector = await self.ConvertTextToEmbeddings(
                texts=[preProcessResponse.cleanQuery]
            )

            docs: list[str] = []
            async with psqlDb.pool.acquire() as conn:
                await conn.set_type_codec(
                    "jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
                )
                rows = await conn.fetch(
                    searchRagQuery, cast(Any, queryVector)[0].embedding, 40
                )

                for row in rows:
                    docs.append(
                        f"For this question : {row.get("question_text")} Answer is {row.get("chunk_text")}"
                    )

            print(preProcessResponse.cleanQuery)

            topRerankedDocs = await self.RerankeDocs(
                request=RerankeRequestModel(
                    query=preProcessResponse.cleanQuery,
                    returnDocuments=True,
                    topN=20,
                    docs=docs,
                )
            )

            topDocs: list[str] = [
                cast(Any, doc.doctext or "") for doc in topRerankedDocs.results
            ]

            systemInst = f"""
                            # Retrieved docs
                            {json.dumps(topDocs, indent=2)}
                You are given:
                - A list `topDocs` retrived from a knowledge base.

                Strict task (follow exactly):
                1. Do **NOT** invent or modify links. Use only URLs present in `topDocs`.
                provide all link which match with user query only importent link which helps user based on user query
                    - give  markdown link  
                3. Keep reply concise. For the whole response (links + explanations) aim to stay under 400 tokens.
                4. if there is no images found just explain based on user query
                5. If there is no answer in the retrieved docs, respond with:
                "We don't have any information about that. do you want me to search through other sources for you ?"


                Formatting constraints:
                - Output plain Markdown only. No raw HTML, no tables.
                - Do not add any links beyond those in `topDocs`.
                - Do not invent URLs or modify titles.
"""

            messages: list[CerebrasChatMessageModel] = [
                CerebrasChatMessageModel(
                    role=CerebrasChatMessageRoleEnum.SYSTEM,
                    content=systemInst,
                ),
                CerebrasChatMessageModel(
                    role=CerebrasChatMessageRoleEnum.USER,
                    content=cast(Any, preProcessResponse.cleanQuery),
                ),
            ]

            response = await self.CerebrasHmisAnswer(messages=messages)

            if response is not None:
                return response
            else:
                return StreamingResponse(
                    iter([b"Sorry, Something went wrong !. Please Try again?"])
                )
