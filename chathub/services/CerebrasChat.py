import cerebras.cloud.sdk
from cerebras.cloud.sdk import AsyncCerebras
from fastapi.responses import StreamingResponse
from chathub.enums import CerebrasChatResponseStatusEnum
from chathub.implementations import CerebrasChatImpl
from chathub.models import (
    CerebrasChatRequestModel,
    CerebrasChatResponseModel,
    CerebrasChatDataModel,
    CerebrasChatUsageModel,
    CerebrasChatChoiceModel,
    CerebrasChatChoiceMessageModel,
)
from cerebras.cloud.sdk import DefaultAioHttpClient
from typing import Any, cast    
from chathub.workers import GetCerebrasApiKey

client = AsyncCerebras(
    api_key=GetCerebrasApiKey(),
    http_client=DefaultAioHttpClient(),
)


class CerebrasChat(CerebrasChatImpl):

    def HandleApiStatusError(self, statusCode: int) -> CerebrasChatResponseModel:
        errorCodes = {
            400: CerebrasChatResponseStatusEnum.BAD_REQUEST,
            401: CerebrasChatResponseStatusEnum.UNAUTHROZIED,
            403: CerebrasChatResponseStatusEnum.PERMISSION_DENIED,
            404: CerebrasChatResponseStatusEnum.NOT_FOUND,
        }
        message = errorCodes.get(
            statusCode, CerebrasChatResponseStatusEnum.SERVER_ERROR
        )
        return CerebrasChatResponseModel(status=message)

    async def Chat(
        self, modelParams: CerebrasChatRequestModel
    ) -> CerebrasChatResponseModel | StreamingResponse:
        try:
            client.api_key = modelParams.apiKey
            create_call = client.chat.completions.create(
                messages=cast(Any, modelParams.messages),
                model=modelParams.model,
                max_completion_tokens=modelParams.maxCompletionTokens,
                stream=modelParams.stream,
                temperature=modelParams.temperature,
                top_p=modelParams.topP,
                seed=modelParams.seed,
                response_format=cast(
                    Any,
                    (
                        None
                        if modelParams.responseFormat is None
                        else {
                            "type": "json_schema",
                            "json_schema": {
                                "name": "schema",
                                "strict": True,
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "response": modelParams.responseFormat
                                    },
                                    "required": ["response"],
                                    "additionalProperties": False,
                                },
                            },
                        }
                    ),
                ),
            )

            if modelParams.stream:
                chatCompletion: Any = await create_call

                async def eventGenerator():
                    buffer = ""
                    try:
                        async for chunk in chatCompletion:
                            if getattr(chunk, "choices", None):
                                delta = getattr(chunk.choices[0], "delta", None)
                                content = getattr(delta, "content", None)
                                if content:
                                    buffer += content
                                    if "\n" in buffer:
                                        yield f"data: {buffer}\n\n"
                                        buffer = ""
                        if buffer:
                            yield f"data: {buffer}\n\n"
                    except Exception as e:
                        yield f"event: error\ndata: {str(e)}\n\n"

                return StreamingResponse(
                    eventGenerator(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                    },
                )

            chatCompletion: Any = await create_call

            choices: list[CerebrasChatChoiceModel] = []
            for ch in chatCompletion.choices:
                choices.append(
                    CerebrasChatChoiceModel(
                        index=ch.index,
                        message=CerebrasChatChoiceMessageModel(
                            role=ch.message.role,
                            content=ch.message.content,
                        ),
                    )
                )

            LLMData = CerebrasChatDataModel(
                id=chatCompletion.id,
                choices=choices,
                created=chatCompletion.created,
                model=chatCompletion.model,
                totalTime=chatCompletion.time_info.total_time,
                usage=CerebrasChatUsageModel(
                    promptTokens=chatCompletion.usage.prompt_tokens,
                    completionTokens=chatCompletion.usage.completion_tokens,
                    totalTokens=chatCompletion.usage.total_tokens,
                ),
            )

            return CerebrasChatResponseModel(
                status=CerebrasChatResponseStatusEnum.SUCCESS,
                content=LLMData.choices[0].message.content,
            )
            

        except cerebras.cloud.sdk.APIConnectionError as e:
            print(e)
            return CerebrasChatResponseModel(
                status=CerebrasChatResponseStatusEnum.SERVER_ERROR
            )
        except cerebras.cloud.sdk.RateLimitError as e:
            print(e)
            return CerebrasChatResponseModel(
                status=CerebrasChatResponseStatusEnum.RATE_LIMIT
            )
        except cerebras.cloud.sdk.APIStatusError as e:
            print(e)
            return self.HandleApiStatusError(e.status_code)
        except Exception as e:
            print(e)
            return CerebrasChatResponseModel(
                status=CerebrasChatResponseStatusEnum.ERROR
            )
