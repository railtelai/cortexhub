


EXTRCT_INFO_FROM_CHUNK_FOR_GRAPH_RAG = r"""
TASK
Return ONLY valid JSON per the schema for ONE input chunk.

INPUT
{ "chunk": "..." }

OUTPUT (conceptual)
{
  "response": {
    "relations": ["..."],
    "questions": ["..."],
    "chunk": "..."
  }
}

RULES
- JSON only. No markdown, no comments, no extra keys.
- Use DOUBLE QUOTES " for all keys and string values (never single quotes).
- Output must be a valid JSON object without line breaks \n or escape sequences.
- No special characters outside valid JSON.
4. Echo the input "chunk" as the value of response.chunk after minimal cleaning:
   - Trim leading/trailing whitespace.
   - Collapse repeated spaces/newlines into a single space.
   - Remove unprintable control characters.
   - Preserve ALL URLs, image links
- Do NOT invent entities.
- Relations: Form ≥9 natural language sentences that clearly express how the entities are related. Each relation must read as a proper sentence including the entities.
- Do NOT include URLs or image tokens in Relations
- If a relation cannot be mapped to a [subject, object], DROP that relation so lengths stay equal.
- Questions: Form possible questions per chunk, all are answerable from chunk only form more then 4 per chunk which has a clear answer in the current chunk.
- Do NOT include URLs or image tokens in questions
"""