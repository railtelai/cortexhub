CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE chunks (
  id UUID NOT NULL,
  text TEXT NOT NULL,
  embedding VECTOR(1024) NOT NULL
);

CREATE TABLE chunk_questions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  chunk_id UUID NOT NULL,
  text TEXT NOT NULL,
  embedding VECTOR(1024) NOT NULL
);



CREATE TABLE chunk_relations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  chunk_id UUID NOT NULL,
  relation TEXT NOT NULL,
  embedding VECTOR(1024) NOT NULL
);


CREATE INDEX idx_chunks_vec_hnsw        ON chunks          USING hnsw (embedding      vector_cosine_ops)   WITH (m=16, ef_construction=300);
CREATE INDEX idx_chunkq_vec_hnsw        ON chunk_questions USING hnsw (embedding  vector_cosine_ops)   WITH (m=16, ef_construction=300);
CREATE INDEX idx_chunkrel_vec_hnsw      ON chunk_relations USING hnsw (embedding  vector_cosine_ops)   WITH (m=16, ef_construction=300);
