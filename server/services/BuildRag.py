from typing import Any
from server.implementations import BuildRagImpl
from raghub.services import BuildRagFromDoc, BuildQaRagFromDoc,BuildYtRag
from raghub.enums import RagBuildProcessEnum

buildRag = BuildRagFromDoc()
buildQaRag = BuildQaRagFromDoc()
buildYtRag = BuildYtRag()

class BuildRag(BuildRagImpl):

    async def BuildRag(self, file: str, db: Any):
        ragResponse = await buildRag.HandleRagBuildProcess(
            file, process=RagBuildProcessEnum.GRAPHRAG
        )

        chunkTexts: list[Any] = []
        chunkQuestions: list[Any] = []
        chunkRelations: list[Any] = []

        if ragResponse is not None:

            for ct in ragResponse.chunks:
                chunkTexts.append((ct.id, ct.text, ct.embedding))
            for q in ragResponse.chunkQuestions:
                chunkQuestions.append((q.id, q.chunkId, q.text, q.embedding))
            for rel in ragResponse.chunkQuestions or []:
                chunkRelations.append((rel.id, rel.chunkId, rel.text, rel.embedding))

            async with db.pool.acquire() as conn:
                if chunkTexts:
                    await conn.executemany(
                        "INSERT INTO chunks (id, text, embedding) VALUES ($1, $2, $3)",
                        chunkTexts,
                    )

                if chunkQuestions:
                    await conn.executemany(
                        "INSERT INTO chunk_questions (id,chunk_id, text, embedding) VALUES ($1, $2, $3,$4)",
                        chunkQuestions,
                    )

                if chunkRelations:
                    await conn.executemany(
                        "INSERT INTO chunk_relations (id,chunk_id, relation, embedding) VALUES ($1, $2, $3, $4)",
                        chunkRelations,
                    )
        
    async def BuildYtRag(self, videoId: str, db: Any):
        ragResponse = await buildYtRag.HandleRagBuildProcess(
            videoId=videoId
        )

        chunkTexts: list[Any] = []
        chunkQuestions: list[Any] = []
        chunkRelations: list[Any] = []

        if ragResponse is not None:

            for ct in ragResponse.chunks:
                chunkTexts.append((ct.id, ct.text, ct.embedding))
            for q in ragResponse.chunkQuestions:
                chunkQuestions.append((q.id, q.chunkId, q.text, q.embedding))
            for rel in ragResponse.chunkQuestions or []:
                chunkRelations.append((rel.id, rel.chunkId, rel.text, rel.embedding))

            async with db.pool.acquire() as conn:
                if chunkTexts:
                    await conn.executemany(
                        "INSERT INTO chunks (id, text, embedding) VALUES ($1, $2, $3)",
                        chunkTexts,
                    )

                if chunkQuestions:
                    await conn.executemany(
                        "INSERT INTO chunk_questions (id,chunk_id, text, embedding) VALUES ($1, $2, $3,$4)",
                        chunkQuestions,
                    )

                if chunkRelations:
                    await conn.executemany(
                        "INSERT INTO chunk_relations (id,chunk_id, relation, embedding) VALUES ($1, $2, $3, $4)",
                        chunkRelations,
                    )
        

    async def BuildQaRag(self, file: str, db: Any):
        ragResponse = await buildQaRag.HandleBuildQaRagProcess(
            file,
        )

        chunkTexts: list[Any] = []
        chunkQuestions: list[Any] = []

        if len(ragResponse.chunks) > 0 and len(ragResponse.questions) > 0:

            for ct in ragResponse.chunks:
                chunkTexts.append((ct.id, ct.text, ct.embedding))
            for q in ragResponse.questions:
                chunkQuestions.append((q.id, q.chunkId, q.text, q.embedding))

            async with db.pool.acquire() as conn:
                if chunkTexts:
                    await conn.executemany(
                        "INSERT INTO chunks (id, text, embedding) VALUES ($1, $2, $3)",
                        chunkTexts,
                    )

                if chunkQuestions:
                    await conn.executemany(
                        "INSERT INTO chunk_questions (id,chunk_id, text, embedding) VALUES ($1, $2, $3,$4)",
                        chunkQuestions,
                    )
