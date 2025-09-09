from typing import Any
from server.implementations import BuildRagImpl
from raghub.services import BuildRagFromDoc
from raghub.enums import RagBuildProcessEnum

buildRag = BuildRagFromDoc()


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
                        "INSERT INTO chunk_relations (id,chunk_id, text, embedding) VALUES ($1, $2, $3, $4)",
                        chunkRelations,
                    )
