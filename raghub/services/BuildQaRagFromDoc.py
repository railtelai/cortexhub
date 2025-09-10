from raghub.implementations import BuildQaRagFromDocImpl
from raghub.models import ExtarctQaResponseModel, HandleBuildQaRagProcessResponseModel
from workers.services import ExtractTextFromDoc
import re
from raghub.models import ConvertTextToEmbeddingResponseModel
import httpx
from raghub.models import GraphRagQuestionModel, GraphRagChunkTextsModel
from uuid import uuid4


class BuildQaRagFromDoc(BuildQaRagFromDocImpl):
    def __init__(self):
        self.extarctTextFromDoc = ExtractTextFromDoc()
        self.batchLength = 50

    def ExtarctQaFromText(self, text: str) -> ExtarctQaResponseModel:
        questions = re.findall(r"<<C1-START>>(.*?)<<C1-END>>", text, re.DOTALL)
        answers = re.findall(r"<<C2-START>>(.*?)<<C2-END>>", text, re.DOTALL)
        additionalAnswers = re.findall(r"<<C3-START>>(.*?)<<C3-END>>", text, re.DOTALL)

        combinedAnswer: list[str] = []
        for ans, addAns in zip(answers, additionalAnswers):
            if addAns != "None":
                combinedAnswer.append(f"{ans} Alternative solution is {addAns}")
            else:
                combinedAnswer.append(ans)
        return ExtarctQaResponseModel(questions=questions, answers=combinedAnswer)

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

    async def HandleBuildQaRagProcess(
        self, file: str
    ) -> HandleBuildQaRagProcessResponseModel:
        text, _ = self.extarctTextFromDoc.ExtractTextFromDoc(docPath=file)
        qa = self.ExtarctQaFromText(text=text)
        chunks: list[GraphRagChunkTextsModel] = []
        questions: list[GraphRagQuestionModel] = []

        for index in range(0, len(qa.questions), self.batchLength):
            queVecRes = await self.ConvertTextToEmbeddings(
                texts=qa.questions[index : index + self.batchLength],
            )
            if queVecRes is not None:
                for idx, q in enumerate(queVecRes):
                    chunkId = uuid4()

                    chunks.append(
                        GraphRagChunkTextsModel(
                            id=chunkId, text=qa.questions[index + idx]
                        )
                    )
                    questions.append(
                        GraphRagQuestionModel(
                            id=uuid4(),
                            chunkId=chunkId,
                            embedding=q.embedding,
                            text=qa.questions[index + idx],
                        )
                    )

        return HandleBuildQaRagProcessResponseModel(chunks=chunks, questions=questions)
