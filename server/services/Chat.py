from typing import Any, cast

from fastapi.responses import StreamingResponse
from chathub.models import CerebrasChatRequestModel, CerebrasChatMessageModel
from chathub.workers import GetCerebrasApiKey, GetCerebrasApiKey1, GetCerebrasApiKey2
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
                model="llama-4-maverick-17b-128e-instruct",
                maxCompletionTokens=500,
                messages=messages,
                temperature=0.0,
                topP=0.0,
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
            if chatResponse.get("cleanquery") is None:
                raise Exception("Exception while extracting relations from chunk")
            

        except Exception as e:
            print("Error occured while extracting realtions from chunk retrying ...")
            print(e)
            messages.append(
                CerebrasChatMessageModel(
                    role=CerebrasChatMessageRoleEnum.USER,
                    content="Please generate a valid json object clean query and type",
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
                    apiKey=GetCerebrasApiKey1(),
                    model="gpt-oss-120b",
                    maxCompletionTokens=15000,
                    messages=messages,
                    stream=True,
                    temperature=0.0,
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
                    apiKey=GetCerebrasApiKey2(),
                    model="gpt-oss-120b",
                    maxCompletionTokens=5000,
                    messages=messages,
                    stream=True,
                    temperature=0.0,
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

                DEFINITIONS (use these exactly):
- PREVIOUS: The current user message is explicitly confirming, continuing, referring to, or asking a follow-up about the immediately prior assistant message (examples below). Includes short confirmations to a prior assistant prompt ("yes", "no", "okay", "continue"), simple follow-ups related to the last assistant answer, common conversational acknowledgements (greetings, thanks) when they are not new search intents, and direct meta-questions about the assistant (who are you, what can you do, version, creator, age, location).
- SEARCH: Any generic question or information request that should trigger the knowledge/RAG pipeline (e.g., factual questions, how-to, dosage, definitions), and any ambiguous short message that is not clearly a PREVIOUS confirmation of the immediate assistant prompt.
- ABUSE_LANG_ERROR: The current user message is abusive, harassing, threatening, or hateful. Consider only the current message content.
- CONTACT_INFO_ERROR: The current user message contains sensitive personal identifiers (phone numbers, emails, national ID/Aadhar, medical record numbers, account numbers, passwords, street addresses, etc.).
- HMIS: The current user message is explicitly about hospital operations, OPD, HMIS platform, patient records, registration, prescriptions, lab reports, billing, hospital workflows, or healthcare-information-system mechanics.

MANDATORY RULES (follow in order):
1. Output EXACTLY valid JSON only. No commentary, no markdown, no extra fields, no wrapper objects, no trailing text.
2. Allowed "type" values are exactly: PREVIOUS, SEARCH, ABUSE_LANG_ERROR, CONTACT_INFO_ERROR, HMIS (uppercase).
3. Use conversation CONTEXT to decide PREVIOUS. PREVIOUS applies only when the immediately prior assistant message explicitly invited confirmation/continuation (e.g., "Do you want me to search through other sources for you?", "Would you like more details?", "Shall I continue?") OR when the user’s current message is an explicit follow-up or direct reference to the previous assistant answer (e.g., "about that", "same", "do that", "yes to previous").
4. If the immediately prior assistant message asked the user directly to confirm/continue/search and the user replies with any short confirmation token (examples: yes, y, sure, okay, continue, no, nah) classify as PREVIOUS and set cleanquery to "(previous)".
5. Treat greetings ("hi", "hello", "hey"), thanks ("thanks", "thank you"), and basic assistant meta-questions ("who are you?", "what can you do?", "how old are you?", "where are you from?", "who created you?", "what is your version?") as PREVIOUS (they are conversational not new search intents).
6. If the current message contains personal/sensitive identifiers, set type = CONTACT_INFO_ERROR (take precedence over HMIS/SEARCH).
7. If the current message is abusive/harassing/threatening, set type = ABUSE_LANG_ERROR (take precedence over HMIS/SEARCH).
8. If the current message is clearly about hospital systems, OPD, patient records, HMIS workflows, set type = HMIS.
9. Otherwise set type = SEARCH.
10. For cleanquery:
    - Return a concise, grammatical English sentence or question summarizing the user's intent (prefer < ~40 tokens).
    - Translate non-English input to English and correct obvious spelling/grammar.
    - Do not include or repeat prior assistant messages verbatim unless you must set cleanquery to "(previous)" per rule 4.
    - If type = PREVIOUS and the immediately prior assistant message invited confirmation/continuation, set "cleanquery" exactly to "(previous)".
    - If type = PREVIOUS but there is no explicit immediate assistant prompt to continue/search, DO NOT guess — set type = SEARCH and normalize the user message into cleanquery.
11. If classification is ambiguous, prefer SEARCH (not HMIS).
12. Validate output: ensure "type" is one of allowed enums. If your internal reasoning would produce any other value, output {"cleanquery":"<normalized text>","type":"SEARCH"} instead.
13. Do not invent or use hidden context. Use only the provided conversation context.
cleanquery can never be empty.
""",
            ),
        ]
        for message in request.messages:
            preProcessMessage.append(
                CerebrasChatMessageModel(
                    content=message.content,
                    role=(
                        CerebrasChatMessageRoleEnum.USER
                        if message.role == "user"
                        else CerebrasChatMessageRoleEnum.ASSISTANT
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
                    content="You are **HMIS AI**  your response should be short and concise not more then 100 tokens ",
                )
            ]

            for message in request.messages:
                generalMessages.append(
                    CerebrasChatMessageModel(
                        content=message.content,
                        role=(
                            CerebrasChatMessageRoleEnum.USER
                            if message.role == "user"
                            else CerebrasChatMessageRoleEnum.ASSISTANT
                        ),
                    )
                )
            generalMessages.append(
                CerebrasChatMessageModel(
                    content=request.query,
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
                    question = row.get("question_text", "")
                    answer = row.get("chunk_text", "")
                    docs.append(f"For this question : {question} Answer is {answer}")

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
