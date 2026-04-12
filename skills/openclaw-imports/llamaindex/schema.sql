-- Multi-tenant Document Management Schema
-- SQLite

BEGIN;

-- Tenants (organizations/businesses)
CREATE TABLE tenants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- Projects within tenants
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    name TEXT NOT NULL,
    description TEXT,
    settings TEXT,                      -- JSON: {"embed_model": "...", "parse_tier": "...", "chunk_size": 512}
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);
CREATE INDEX idx_projects_tenant ON projects(tenant_id);

-- Documents (raw file references + metadata)
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,           -- local path to raw file
    file_type TEXT NOT NULL,           -- pdf, docx, txt, etc.
    file_size INTEGER,                 -- bytes
    md5_hash TEXT,                     -- for deduplication
    mime_type TEXT,
    
    -- LlamaParse metadata
    parse_status TEXT DEFAULT 'pending' CHECK(parse_status IN ('pending', 'parsing', 'done', 'failed')),
    parse_tier TEXT DEFAULT 'standard', -- standard or agentic
    parse_error TEXT,
    parse_job_id TEXT,                 -- LlamaCloud job ID if tracked
    pages_parsed INTEGER DEFAULT 0,
    parsed_markdown_path TEXT,         -- path to parsed markdown
    
    -- Chroma metadata
    chroma_collection TEXT,            -- which Chroma collection
    chunks_indexed INTEGER DEFAULT 0,
    index_status TEXT DEFAULT 'pending' CHECK(index_status IN ('pending', 'indexing', 'done', 'failed')),
    index_error TEXT,
    
    -- Content metadata
    language TEXT,
    page_count INTEGER,
    
    -- Audit
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT 0        -- soft delete
);
CREATE INDEX idx_documents_project ON documents(project_id);
CREATE INDEX idx_documents_status ON documents(parse_status, index_status);
CREATE INDEX idx_documents_hash ON documents(md5_hash);

-- Chunks (individual parsed+chunked segments)
CREATE TABLE chunks (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id),
    chunk_index INTEGER NOT NULL,      -- order within document
    text TEXT NOT NULL,
    char_count INTEGER,
    token_count_estimate INTEGER,
    
    -- Chroma vector ID
    chroma_id TEXT,
    
    -- Page reference
    page_number INTEGER,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_chunks_document ON chunks(document_id);
CREATE INDEX idx_chunks_chroma ON chunks(chroma_id);

-- Retrieval logs (for audit + billing)
CREATE TABLE retrieval_logs (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    project_id TEXT REFERENCES projects(id),
    document_id TEXT REFERENCES documents(id),
    
    query_text TEXT NOT NULL,
    query_embedding_id TEXT,           -- reference stored embedding
    
    results_returned INTEGER,
    chunks_cited TEXT,                 -- JSON array of chunk IDs
    
    response_time_ms INTEGER,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_retrieval_tenant ON retrieval_logs(tenant_id, created_at);
CREATE INDEX idx_retrieval_project ON retrieval_logs(project_id);

-- API keys per tenant
CREATE TABLE api_keys (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    key_hash TEXT NOT NULL UNIQUE,     -- SHA256 of actual key
    key_name TEXT,                      -- "production", "development", etc.
    permissions TEXT,                   -- JSON: ["read", "write", "admin"]
    last_used_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    is_active BOOLEAN DEFAULT 1
);
CREATE INDEX idx_apikeys_tenant ON api_keys(tenant_id);
CREATE INDEX idx_apikeys_hash ON api_keys(key_hash);

-- Skills created and stored
CREATE TABLE skills (
    id TEXT PRIMARY KEY,
    tenant_id TEXT REFERENCES tenants(id),
    name TEXT NOT NULL,
    version TEXT DEFAULT '1.0.0',
    file_path TEXT NOT NULL,
    description TEXT,
    category TEXT,                     -- parsing, analysis, writing, visualization, orchestration
    tags TEXT,                         -- JSON array of tags
    created_by TEXT,                   -- 'user' or agent name
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);
CREATE INDEX idx_skills_tenant ON skills(tenant_id);
CREATE INDEX idx_skills_category ON skills(category);

-- Every LLM inference call (for cost tracking + audit)
CREATE TABLE inference_logs (
    id TEXT PRIMARY KEY,
    tenant_id TEXT REFERENCES tenants(id),
    session_id TEXT,

    -- What model
    provider TEXT NOT NULL,            -- openai, anthropic, ollama, llamacloud, etc.
    model TEXT NOT NULL,               -- gpt-4o, claude-3-sonnet, etc.

    -- Tokens & cost
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER GENERATED ALWAYS AS (prompt_tokens + completion_tokens) STORED,
    cost_usd REAL DEFAULT 0,

    -- Latency
    latency_ms INTEGER,

    -- Context
    task_type TEXT,                    -- parsing, analysis, writing, query, rag, etc.
    skill_used TEXT,                   -- which skill triggered this call
    agent_name TEXT,                   -- which agent made the call
    project_id TEXT REFERENCES projects(id),

    -- Request/response for debugging
    request_summary TEXT,               -- truncated first 500 chars of prompt
    error TEXT,                        -- error message if failed

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_inference_tenant ON inference_logs(tenant_id, created_at);
CREATE INDEX idx_inference_session ON inference_logs(session_id);
CREATE INDEX idx_inference_cost ON inference_logs(tenant_id, cost_usd);
CREATE INDEX idx_inference_provider ON inference_logs(provider, model);

-- All files created by agents or manual upload
CREATE TABLE workspace_files (
    id TEXT PRIMARY KEY,
    tenant_id TEXT REFERENCES tenants(id),
    project_id TEXT REFERENCES projects(id),
    document_id TEXT REFERENCES documents(id),  -- if derived from a document

    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,          -- skill, script, document, markdown, data, image, etc.
    file_size INTEGER,                -- bytes
    mime_type TEXT,

    -- Origin
    created_by TEXT,                  -- agent name or 'manual'
    purpose TEXT,                     -- what it was used for
    parent_file_id TEXT,              -- for derived files (e.g., parsed markdown from PDF)
    skill_id TEXT REFERENCES skills(id),  -- if created by a skill

    -- Content hash for deduplication
    content_hash TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT 0
);
CREATE INDEX idx_files_project ON workspace_files(project_id);
CREATE INDEX idx_files_type ON workspace_files(file_type);
CREATE INDEX idx_files_tenant ON workspace_files(tenant_id);
CREATE INDEX idx_files_parent ON workspace_files(parent_file_id);

-- Subagent sessions (for orchestration tracking)
CREATE TABLE agent_sessions (
    id TEXT PRIMARY KEY,
    tenant_id TEXT REFERENCES tenants(id),
    parent_session_id TEXT,            -- parent orchestrator session
    agent_name TEXT NOT NULL,          -- parser, analyst, writer, etc.
    skill_id TEXT REFERENCES skills(id),

    status TEXT DEFAULT 'running' CHECK(status IN ('running', 'done', 'failed', 'cancelled')),
    task_summary TEXT,                 -- what this agent was asked to do

    -- Timing
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    duration_ms INTEGER,

    -- Output
    result_summary TEXT,               -- truncated result
    error TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_sessions_tenant ON agent_sessions(tenant_id);
CREATE INDEX idx_sessions_parent ON agent_sessions(parent_session_id);

COMMIT;
