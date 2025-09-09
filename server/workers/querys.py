searchRagQuery = """



WITH q AS (
  SELECT $1::vector AS query
),
top_chunks AS (
  SELECT c.id AS chunk_id, c.text, 1.0 - (c.embedding <#> q.query) AS score, 'chunk' AS source
  FROM q
  CROSS JOIN LATERAL (
    SELECT * FROM grag.chunks
    ORDER BY embedding <#> q.query
    LIMIT $2
  ) c
),
top_questions AS (
  SELECT cq.chunk_id, ch.text, 1.0 - (cq.embedding <#> q.query) AS score, 'question' AS source
  FROM q
  CROSS JOIN LATERAL (
    SELECT * FROM grag.chunk_questions
    ORDER BY embedding <#> q.query
    LIMIT $2
  ) cq
  JOIN grag.chunks ch ON ch.id = cq.chunk_id
),
top_relations AS (
  SELECT cr.chunk_id, ch.text, 1.0 - (cr.embedding <#> q.query) AS score, 'relation' AS source
  FROM q
  CROSS JOIN LATERAL (
    SELECT * FROM grag.chunk_relations
    ORDER BY embedding <#> q.query
    LIMIT $2
  ) cr
  JOIN grag.chunks ch ON ch.id = cr.chunk_id
),
all_matches AS (
  SELECT * FROM top_chunks
  UNION ALL
  SELECT * FROM top_questions
  UNION ALL
  SELECT * FROM top_relations
)
SELECT chunk_id, text, MAX(score) AS best_score, array_agg(DISTINCT source) AS matched_sources
FROM all_matches
GROUP BY chunk_id, text
ORDER BY best_score DESC
LIMIT $2;


"""