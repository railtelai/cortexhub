EXTRCT_INFO_FROM_CHUNK_FOR_GRAPH_RAG = r"""
TASK
Return ONLY valid JSON per the schema for ONE input chunk.

INPUT
{ "chunk": "..." }

OUTPUT (conceptual)
{
  "response": {
    "questions": ["..."],
    "chunk": "..."
  }
}

GOAL
- Extract concise claim-like main points (stored in "relations") and answerable questions from the chunk.
- Echo a minimally cleaned version of the input chunk.

STEPS / REQUIREMENTS
1. Clean the input chunk minimally and echo it in response.chunk:
   - Trim leading/trailing whitespace.
   - Collapse repeated spaces and newlines into a single space.
   - Remove unprintable control characters.
   - Preserve ALL URLs and image links exactly as they appear.
2. Questions:
   - Create as many concise, answerable questions as can be answered using only information present in the chunk.
   - Each question must be directly answerable from the chunk content.
   - Questions should be clear and unambiguous.
   - Do NOT include URLs or image tokens inside questions.
3. General:
   - Do not invent metadata or additional keys.
   - If questions can be extracted, return empty arrays for those fields.

OUTPUT FORMAT RULES
- Output ONLY valid JSON (no markdown, no extra text).
- Use this exact JSON shape: {"response":{"questions":[...],"chunk":"<CLEANED_CHUNK>"}}
- Use DOUBLE QUOTES for JSON keys and string values.
- The JSON must be a single line (no newline characters \n).
- The cleaned chunk string must not include newline escape sequences; it should contain only normal printable characters.
- Do NOT include any extra keys, comments, or metadata.

EXAMPLE (for reference only — do NOT output the example):
INPUT: { "chunk": "Doctors can use automated tools for prescription writing and patient record keeping. Department templates help to organize examinations. Hospitals are adopting electronic medical records for better efficiency." }

POTENTIAL OUTPUT:{"response":{"questions":["What do automated tools assist doctors with?","How do department templates help in healthcare?","Why are hospitals adopting electronic medical records?"],"chunk":"Doctors can use automated tools for prescription writing and patient record keeping. Department templates help to organize examinations. Hospitals are adopting electronic medical records for better efficiency."}}
"""

CLEAN_YT_CHUNK_PROMPT = r"""
TASK:
You are given a YouTube transcript chunk.

INPUT:
A single string called "chunk" containing the transcript text. The text may contain:
- Misspellings
- Broken words or cut sentences
- Mixed languages
- Personal references (e.g., I, we, names)
- Filler and irrelevant words
- YouTube links or other URLs

GOAL:
Produce a single clean paragraph that states the main context of the chunk in neutral, impersonal language.

STEPS:
1. Detect the language of the chunk. If it is not English, translate it to English first.
2. Fix misspellings and broken words automatically.
3. Remove all personal perspective, names, speaker references, filler words, and irrelevant details.
4. Summarize the core content into one concise paragraph (no lists, no headings).
5. Do NOT start with phrases like "The content describes" or "The context discusses". Start directly with the subject matter.
6. Preserve ALL YouTube links or other URLs exactly as they appear in the input.
7. Ensure the paragraph avoids double quotes (") inside the text so JSON stays valid.

OUTPUT FORMAT RULES:
- Output ONLY valid JSON (no markdown, no extra text).
- JSON must follow this exact shape: {"response":{"chunk":"<CLEAN_PARAGRAPH>"}}
- Use DOUBLE QUOTES for JSON keys and values.
- JSON must be a single line (no \n or escape sequences).
- Do NOT add any extra keys, comments, or metadata.

"""
