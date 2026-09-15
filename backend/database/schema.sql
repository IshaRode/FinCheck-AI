-- FinCheck AI: Supabase PostgreSQL + pgvector Schema
-- Uses halfvec(2048) for NVIDIA NeMo Retriever embeddings (nvidia/nemotron-3-embed-1b)

-- 1. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Documents Table
CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(128) PRIMARY KEY,
    document_name VARCHAR(512) NOT NULL,
    document_type VARCHAR(64) NOT NULL,
    source VARCHAR(256) NOT NULL,
    source_dataset VARCHAR(64) NOT NULL,
    issued_date DATE,
    regulation_area VARCHAR(256),
    applicable_to TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast lookup by source_dataset / regulation_area
CREATE INDEX IF NOT EXISTS idx_documents_source_dataset ON documents (source_dataset);
CREATE INDEX IF NOT EXISTS idx_documents_regulation_area ON documents (regulation_area);

-- 3. Document Chunks Table
CREATE TABLE IF NOT EXISTS document_chunks (
    id VARCHAR(128) PRIMARY KEY,
    document_id VARCHAR(128) NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_id VARCHAR(128) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    total_chunks_in_doc INTEGER NOT NULL,
    token_count INTEGER NOT NULL,
    page_number INTEGER,
    section VARCHAR(256),
    embedding halfvec(2048),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index foreign keys
CREATE INDEX IF NOT EXISTS idx_document_chunks_doc_id ON document_chunks (document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_chunk_id ON document_chunks (chunk_id);

-- 4. HNSW Vector Index on halfvec(2048) using Cosine Similarity
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_hnsw
ON document_chunks USING hnsw (embedding halfvec_cosine_ops);

-- 5. Evaluation Questions Table (Kept separate from document retrieval corpus)
CREATE TABLE IF NOT EXISTS evaluation_questions (
    id VARCHAR(128) PRIMARY KEY,
    question TEXT NOT NULL,
    expected_answer TEXT NOT NULL,
    source VARCHAR(256),
    dataset_source VARCHAR(64) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evaluation_questions_dataset_source ON evaluation_questions (dataset_source);

-- 6. Vector Search Function / RPC
CREATE OR REPLACE FUNCTION match_document_chunks (
    query_embedding halfvec(2048),
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    chunk_id VARCHAR(128),
    document_id VARCHAR(128),
    content TEXT,
    metadata JSONB,
    document_name VARCHAR(512),
    source VARCHAR(256),
    source_dataset VARCHAR(64),
    section VARCHAR(256),
    page_number INTEGER,
    distance FLOAT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.chunk_id,
        dc.document_id,
        dc.content,
        dc.metadata,
        d.document_name,
        d.source,
        d.source_dataset,
        dc.section,
        dc.page_number,
        (dc.embedding <=> query_embedding)::FLOAT AS distance,
        (1 - (dc.embedding <=> query_embedding))::FLOAT AS similarity
    FROM document_chunks dc
    JOIN documents d ON dc.document_id = d.id
    WHERE dc.embedding IS NOT NULL
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
