


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
- Relations: Form ≥15 natural language sentences that clearly express how the entities are related. Each relation must read as a proper sentence including the entities.
- Do NOT include URLs or image tokens in Relations
- If a relation cannot be mapped to a [subject, object], DROP that relation so lengths stay equal.
- Questions: Form possible questions per chunk, all are answerable from chunk only form more then 15 per chunk which has a clear answer in the current chunk.
- Do NOT include URLs or image tokens in questions
"""



EXTRCT_INFO_FROM_CHUNK_YT_VIDEO = r"""
TASK
Return ONLY valid JSON per schema for ONE text chunk.

INPUT
{ "chunk": "..." }

OUTPUT
{
  "response": {
    "relations": ["..."],
    "questions": ["..."],
    "chunk": "..."
  }
}

RULES
- JSON only, no markdown or comments.
- Use DOUBLE quotes.
- "chunk": clean text (trim, collapse spaces, fix broken words, remove control chars), detect source language and translate fully to English if not already, and KEEP YouTube URL if present.
- THE ENTIRE OUTPUT (chunk, relations, and questions) MUST BE IN ENGLISH — no non-English words or transliterations.
- Do NOT drop or alter the YouTube URL.
- Exclude speaker identifiers, personal mentions (e.g., "I am ..."), or meta-references like "in this video" or "the speaker said". Keep only the main descriptive/contextual content.
- Relations: ≥8 natural-language sentences describing relationships or statements that are explicitly present or can be directly paraphrased from the chunk. Focus only on the actual content, not on who is speaking or that it is a video. No URLs.
- Questions: ≥8 questions that are directly answerable from information present in the chunk (explicitly stated or direct paraphrase). Do not invent questions about things not in the chunk. No URLs.
- Keep relations and questions strictly grounded in the chunk’s content. Do not add outside information, speculation, or analysis.
"""
