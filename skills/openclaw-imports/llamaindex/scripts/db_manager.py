#!/usr/bin/env python3
"""
Document Management Database CLI
Usage: python db_manager.py <command> [options]

Supports: tenants, projects, documents, chunks, api_keys, skills,
          inference_logs, workspace_files, agent_sessions
"""

import sqlite3
import json
import hashlib
import secrets
import argparse
import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid4


DB_PATH = Path(__file__).parent.parent / "data" / "documents.db"


def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database with schema."""
    schema_path = Path(__file__).parent.parent / "schema.sql"
    conn = get_db()
    conn.executescript(schema_path.read_text())
    conn.close()
    print(f"✅ Database initialized at {DB_PATH}")


def generate_api_key() -> tuple[str, str]:
    """Generate a new API key. Returns (key, hash)."""
    key = f"sk_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    return key, key_hash


# =============================================================================
# TENANTS
# =============================================================================

def create_tenant(name: str) -> dict:
    conn = get_db()
    tenant_id = f"tenant_{uuid4().hex[:12]}"
    conn.execute("INSERT INTO tenants (id, name) VALUES (?, ?)", (tenant_id, name))
    conn.commit()
    conn.close()
    return {"id": tenant_id, "name": name}


def list_tenants() -> list:
    conn = get_db()
    rows = conn.execute("SELECT * FROM tenants WHERE is_active = 1").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_tenant(tenant_id: str) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM tenants WHERE id = ?", (tenant_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# =============================================================================
# PROJECTS
# =============================================================================

def create_project(tenant_id: str, name: str, description: str = None, settings: dict = None) -> dict:
    conn = get_db()
    project_id = f"proj_{uuid4().hex[:12]}"
    conn.execute(
        "INSERT INTO projects (id, tenant_id, name, description, settings) VALUES (?, ?, ?, ?, ?)",
        (project_id, tenant_id, name, description, json.dumps(settings) if settings else None)
    )
    conn.commit()
    conn.close()
    return {"id": project_id, "tenant_id": tenant_id, "name": name, "settings": settings}


def list_projects(tenant_id: str) -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM projects WHERE tenant_id = ? AND is_active = 1",
        (tenant_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_project(project_id: str) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_project_settings(project_id: str) -> dict:
    """Get project settings as a dict, with defaults."""
    project = get_project(project_id)
    defaults = {
        "embed_model": "local:BAAI/bge-small-en-v1.5",
        "parse_tier": "agentic",
        "chunk_size": 512,
        "chunk_overlap": 50,
    }
    if not project or not project.get('settings'):
        return defaults
    try:
        stored = json.loads(project['settings'])
        return {**defaults, **stored}
    except:
        return defaults


def update_project_settings(project_id: str, settings: dict) -> dict:
    """Update project settings (merges with existing)."""
    conn = get_db()
    existing = conn.execute("SELECT settings FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not existing:
        conn.close()
        return {"error": "Project not found"}
    
    merged = {}
    if existing['settings']:
        try:
            merged = json.loads(existing['settings'])
        except:
            pass
    merged.update(settings)
    
    conn.execute(
        "UPDATE projects SET settings = ?, updated_at = ? WHERE id = ?",
        (json.dumps(merged), datetime.now().isoformat(), project_id)
    )
    conn.commit()
    conn.close()
    return {"id": project_id, "settings": merged}


# =============================================================================
# DOCUMENTS
# =============================================================================

def add_document(
    project_id: str,
    file_path: str,
    parse_tier: str = "fast",
    parse_status: str = "pending"
) -> dict:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    conn = get_db()
    doc_id = f"doc_{uuid4().hex[:12]}"
    md5 = hashlib.md5(path.read_bytes()).hexdigest()
    
    # Deduplication check
    existing = conn.execute(
        "SELECT id FROM documents WHERE project_id = ? AND md5_hash = ? AND is_deleted = 0",
        (project_id, md5)
    ).fetchone()
    if existing:
        conn.close()
        return {"error": "Document already exists", "existing_id": existing[0]}
    
    conn.execute("""
        INSERT INTO documents 
        (id, project_id, file_name, file_path, file_type, file_size, md5_hash, parse_tier, parse_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        doc_id, project_id, path.name, str(path.absolute()),
        path.suffix.lstrip('.'), path.stat().st_size, md5, parse_tier, parse_status
    ))
    conn.commit()
    conn.close()
    return {"id": doc_id, "file_name": path.name}


def update_document_status(doc_id: str, **fields) -> dict:
    allowed = ['parse_status', 'parse_error', 'pages_parsed', 'parsed_markdown_path',
               'index_status', 'index_error', 'chunks_indexed', 'chroma_collection',
               'language', 'page_count']
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return {"error": "No valid fields to update"}
    updates['updated_at'] = datetime.now().isoformat()
    
    conn = get_db()
    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
    conn.execute(f"UPDATE documents SET {set_clause} WHERE id = ?", (*updates.values(), doc_id))
    conn.commit()
    conn.close()
    return {"id": doc_id, "updated": updates}


def list_documents(project_id: str, include_deleted: bool = False) -> list:
    conn = get_db()
    query = "SELECT * FROM documents WHERE project_id = ?"
    if not include_deleted:
        query += " AND is_deleted = 0"
    rows = conn.execute(query, (project_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_document(doc_id: str) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_document(doc_id: str, hard: bool = False) -> dict:
    conn = get_db()
    if hard:
        conn.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    else:
        conn.execute("UPDATE documents SET is_deleted = 1 WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()
    return {"id": doc_id, "deleted": True}


# =============================================================================
# CHUNKS
# =============================================================================

def add_chunks(document_id: str, chunks: list[dict]) -> list:
    conn = get_db()
    inserted = []
    for chunk in chunks:
        chunk_id = f"chunk_{uuid4().hex[:12]}"
        conn.execute("""
            INSERT INTO chunks (id, document_id, chunk_index, text, char_count, page_number, chroma_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            chunk_id, document_id, chunk['chunk_index'], chunk['text'],
            chunk.get('char_count', len(chunk['text'])),
            chunk.get('page_number'), chunk.get('chroma_id')
        ))
        inserted.append(chunk_id)
    conn.commit()
    conn.close()
    return inserted


def list_chunks(document_id: str) -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM chunks WHERE document_id = ? ORDER BY chunk_index",
        (document_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# =============================================================================
# API KEYS
# =============================================================================

def create_api_key(tenant_id: str, key_name: str = None, permissions: list = None) -> dict:
    key, key_hash = generate_api_key()
    conn = get_db()
    key_id = f"key_{uuid4().hex[:12]}"
    conn.execute("""
        INSERT INTO api_keys (id, tenant_id, key_hash, key_name, permissions)
        VALUES (?, ?, ?, ?, ?)
    """, (key_id, tenant_id, key_hash, key_name, json.dumps(permissions or ["read"])))
    conn.commit()
    conn.close()
    return {"id": key_id, "key": key, "key_name": key_name, "tenant_id": tenant_id}


def verify_api_key(key: str) -> dict | None:
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    conn = get_db()
    row = conn.execute("""
        SELECT ak.*, t.name as tenant_name 
        FROM api_keys ak JOIN tenants t ON ak.tenant_id = t.id
        WHERE ak.key_hash = ? AND ak.is_active = 1 AND t.is_active = 1
        AND (ak.expires_at IS NULL OR ak.expires_at > datetime('now'))
    """, (key_hash,)).fetchone()
    if row:
        conn.execute("UPDATE api_keys SET last_used_at = CURRENT_TIMESTAMP WHERE id = ?", (row['id'],))
        conn.commit()
    conn.close()
    return dict(row) if row else None


def list_api_keys(tenant_id: str) -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT id, tenant_id, key_name, permissions, last_used_at, created_at, expires_at, is_active FROM api_keys WHERE tenant_id = ?",
        (tenant_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# =============================================================================
# SKILLS
# =============================================================================

def register_skill(
    tenant_id: str = None,
    name: str = None,
    file_path: str = None,
    description: str = None,
    category: str = None,
    tags: list = None,
    created_by: str = "manual"
) -> dict:
    conn = get_db()
    skill_id = f"skill_{uuid4().hex[:12]}"
    version = "1.0.0"
    
    # Check if skill with same name exists for tenant
    existing = conn.execute(
        "SELECT id, version FROM skills WHERE tenant_id IS ? AND name = ? AND is_active = 1",
        (tenant_id, name)
    ).fetchone()
    if existing:
        # Bump version
        major, minor, patch = existing['version'].split('.')
        patch = str(int(patch) + 1)
        version = f"{major}.{minor}.{patch}"
        skill_id = existing['id']
        conn.execute(
            "UPDATE skills SET version = ?, updated_at = ? WHERE id = ?",
            (version, datetime.now().isoformat(), skill_id)
        )
    else:
        conn.execute("""
            INSERT INTO skills (id, tenant_id, name, version, file_path, description, category, tags, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (skill_id, tenant_id, name, version, file_path, description, category, json.dumps(tags or []), created_by))
    
    conn.commit()
    conn.close()
    return {"id": skill_id, "name": name, "version": version}


def list_skills(tenant_id: str = None, category: str = None) -> list:
    conn = get_db()
    query = "SELECT * FROM skills WHERE is_active = 1"
    params = []
    if tenant_id:
        query += " AND (tenant_id IS ? OR tenant_id IS NULL)"
        params.append(tenant_id)
    if category:
        query += " AND category = ?"
        params.append(category)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_skill(skill_id: str) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM skills WHERE id = ?", (skill_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def deactivate_skill(skill_id: str) -> dict:
    conn = get_db()
    conn.execute("UPDATE skills SET is_active = 0 WHERE id = ?", (skill_id,))
    conn.commit()
    conn.close()
    return {"id": skill_id, "deactivated": True}


# =============================================================================
# INFERENCE LOGS
# =============================================================================

def log_inference(
    tenant_id: str = None,
    provider: str = None,
    model: str = None,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    cost_usd: float = 0,
    latency_ms: int = None,
    task_type: str = None,
    skill_used: str = None,
    agent_name: str = None,
    session_id: str = None,
    project_id: str = None,
    request_summary: str = None,
    error: str = None
) -> dict:
    conn = get_db()
    log_id = f"inflog_{uuid4().hex[:12]}"
    conn.execute("""
        INSERT INTO inference_logs 
        (id, tenant_id, provider, model, prompt_tokens, completion_tokens, cost_usd,
         latency_ms, task_type, skill_used, agent_name, session_id, project_id, request_summary, error)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        log_id, tenant_id, provider, model, prompt_tokens, completion_tokens, cost_usd,
        latency_ms, task_type, skill_used, agent_name, session_id, project_id,
        (request_summary or "")[:500] if request_summary else None,
        error
    ))
    conn.commit()
    conn.close()
    return {"id": log_id}


def get_inference_stats(tenant_id: str = None, days: int = 30) -> dict:
    conn = get_db()
    query = """
        SELECT 
            COUNT(*) as total_calls,
            SUM(prompt_tokens) as total_prompt_tokens,
            SUM(completion_tokens) as total_completion_tokens,
            SUM(total_tokens) as total_tokens,
            SUM(cost_usd) as total_cost_usd,
            AVG(latency_ms) as avg_latency_ms,
            provider,
            model
        FROM inference_logs
        WHERE created_at >= datetime('now', '-' || ? || ' days')
    """
    params = [days]
    if tenant_id:
        query += " AND tenant_id = ?"
        params.append(tenant_id)
    query += " GROUP BY provider, model"
    
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return {"period_days": days, "by_model": [dict(r) for r in rows]}


def get_inference_logs(tenant_id: str = None, limit: int = 100) -> list:
    conn = get_db()
    query = "SELECT * FROM inference_logs"
    params = []
    if tenant_id:
        query += " WHERE tenant_id = ?"
        params.append(tenant_id)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# =============================================================================
# WORKSPACE FILES
# =============================================================================

def register_file(
    tenant_id: str = None,
    project_id: str = None,
    document_id: str = None,
    file_path: str = None,
    file_name: str = None,
    file_type: str = None,
    created_by: str = "manual",
    purpose: str = None,
    parent_file_id: str = None,
    skill_id: str = None,
    content_hash: str = None
) -> dict:
    path = Path(file_path) if file_path else None
    file_id = f"file_{uuid4().hex[:12]}"
    
    conn = get_db()
    conn.execute("""
        INSERT INTO workspace_files 
        (id, tenant_id, project_id, document_id, file_path, file_name, file_type, file_size,
         created_by, purpose, parent_file_id, skill_id, content_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        file_id, tenant_id, project_id, document_id,
        file_path, file_name or (path.name if path else None),
        file_type, path.stat().st_size if path and path.exists() else None,
        created_by, purpose, parent_file_id, skill_id, content_hash
    ))
    conn.commit()
    conn.close()
    return {"id": file_id, "file_name": file_name or path.name if path else None}


def list_files(tenant_id: str = None, project_id: str = None, file_type: str = None) -> list:
    conn = get_db()
    query = "SELECT * FROM workspace_files WHERE is_deleted = 0"
    params = []
    if tenant_id:
        query += " AND tenant_id = ?"
        params.append(tenant_id)
    if project_id:
        query += " AND project_id = ?"
        params.append(project_id)
    if file_type:
        query += " AND file_type = ?"
        params.append(file_type)
    query += " ORDER BY created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_file(file_id: str, hard: bool = False) -> dict:
    conn = get_db()
    if hard:
        conn.execute("DELETE FROM workspace_files WHERE id = ?", (file_id,))
    else:
        conn.execute("UPDATE workspace_files SET is_deleted = 1 WHERE id = ?", (file_id,))
    conn.commit()
    conn.close()
    return {"id": file_id, "deleted": True}


# =============================================================================
# AGENT SESSIONS
# =============================================================================

def start_agent_session(
    tenant_id: str = None,
    parent_session_id: str = None,
    agent_name: str = None,
    skill_id: str = None,
    task_summary: str = None
) -> dict:
    conn = get_db()
    session_id = f"session_{uuid4().hex[:12]}"
    conn.execute("""
        INSERT INTO agent_sessions (id, tenant_id, parent_session_id, agent_name, skill_id, task_summary, status)
        VALUES (?, ?, ?, ?, ?, ?, 'running')
    """, (session_id, tenant_id, parent_session_id, agent_name, skill_id, task_summary))
    conn.commit()
    conn.close()
    return {"id": session_id, "status": "running"}


def complete_agent_session(
    session_id: str,
    result_summary: str = None,
    error: str = None,
    status: str = "done"
) -> dict:
    conn = get_db()
    conn.execute("""
        UPDATE agent_sessions 
        SET status = ?, result_summary = ?, error = ?,
            completed_at = CURRENT_TIMESTAMP,
            duration_ms = CAST((julianday(CURRENT_TIMESTAMP) - julianday(started_at)) * 86400000 AS INTEGER)
        WHERE id = ?
    """, (status, (result_summary or "")[:500] if result_summary else None, error, session_id))
    conn.commit()
    conn.close()
    return {"id": session_id, "status": status}


def get_agent_sessions(parent_session_id: str = None, tenant_id: str = None) -> list:
    conn = get_db()
    query = "SELECT * FROM agent_sessions WHERE 1=1"
    params = []
    if parent_session_id:
        query += " AND parent_session_id = ?"
        params.append(parent_session_id)
    if tenant_id:
        query += " AND tenant_id = ?"
        params.append(tenant_id)
    query += " ORDER BY started_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# =============================================================================
# RETRIEVAL LOGS
# =============================================================================

def log_retrieval(
    tenant_id: str, project_id: str = None, document_id: str = None,
    query_text: str = None, results_returned: int = 0,
    chunks_cited: list = None, response_time_ms: int = None
) -> dict:
    conn = get_db()
    log_id = f"log_{uuid4().hex[:12]}"
    conn.execute("""
        INSERT INTO retrieval_logs 
        (id, tenant_id, project_id, document_id, query_text, results_returned, chunks_cited, response_time_ms)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (log_id, tenant_id, project_id, document_id, query_text, results_returned, json.dumps(chunks_cited or []), response_time_ms))
    conn.commit()
    conn.close()
    return {"id": log_id}


# =============================================================================
# STATS
# =============================================================================

def get_stats(tenant_id: str = None) -> dict:
    conn = get_db()
    
    base_where = "WHERE is_active = 1" if not tenant_id else f"WHERE tenant_id = '{tenant_id}' AND is_active = 1"
    
    stats = {
        "total_tenants": conn.execute("SELECT COUNT(*) FROM tenants WHERE is_active = 1").fetchone()[0],
        "total_projects": conn.execute(f"SELECT COUNT(*) FROM projects {base_where}").fetchone()[0],
        "total_documents": conn.execute(f"SELECT COUNT(*) FROM documents {base_where.replace('is_active', 'is_deleted = 0 AND is_active') if tenant_id else 'WHERE is_deleted = 0'}").fetchone()[0],
        "total_chunks": conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0],
        "total_skills": conn.execute("SELECT COUNT(*) FROM skills WHERE is_active = 1").fetchone()[0],
        "total_inference_calls": conn.execute("SELECT COUNT(*) FROM inference_logs").fetchone()[0],
        "total_files": conn.execute("SELECT COUNT(*) FROM workspace_files WHERE is_deleted = 0").fetchone()[0],
        "total_agent_sessions": conn.execute("SELECT COUNT(*) FROM agent_sessions").fetchone()[0],
    }
    conn.close()
    return stats


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Document Management DB")
    sub = parser.add_subparsers(dest="cmd", help="Available commands")
    
    # init
    sub.add_parser("init", help="Initialize database")
    
    # tenants
    sub.add_parser("list-tenants", help="List all tenants")
    p = sub.add_parser("create-tenant", help="Create tenant")
    p.add_argument("name")
    
    # projects
    p = sub.add_parser("create-project", help="Create project")
    p.add_argument("tenant_id")
    p.add_argument("name")
    p.add_argument("--desc", dest="description")
    p.add_argument("--settings", help="JSON settings string")
    p = sub.add_parser("list-projects", help="List projects")
    p.add_argument("tenant_id")
    p = sub.add_parser("get-project", help="Get project")
    p.add_argument("project_id")
    p = sub.add_parser("update-project-settings", help="Update project settings")
    p.add_argument("project_id")
    p.add_argument("--settings", required=True, help="JSON settings string")
    
    # documents
    p = sub.add_parser("add-doc", help="Add document")
    p.add_argument("project_id")
    p.add_argument("file_path")
    p.add_argument("--tier", default="standard")
    p = sub.add_parser("list-docs", help="List documents")
    p.add_argument("project_id")
    p = sub.add_parser("get-doc", help="Get document")
    p.add_argument("doc_id")
    p = sub.add_parser("delete-doc", help="Delete document")
    p.add_argument("doc_id")
    p.add_argument("--hard", action="store_true")
    
    # skills
    p = sub.add_parser("register-skill", help="Register a skill")
    p.add_argument("--tenant-id")
    p.add_argument("--name", required=True)
    p.add_argument("--file-path", required=True)
    p.add_argument("--desc")
    p.add_argument("--category")
    p.add_argument("--tags", nargs="+")
    p.add_argument("--created-by", default="manual")
    p = sub.add_parser("list-skills", help="List skills")
    p.add_argument("--tenant-id")
    p.add_argument("--category")
    p = sub.add_parser("get-skill", help="Get skill")
    p.add_argument("skill_id")
    
    # inference
    p = sub.add_parser("log-inference", help="Log an inference call")
    p.add_argument("--tenant-id")
    p.add_argument("--provider", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--prompt-tokens", type=int, default=0)
    p.add_argument("--completion-tokens", type=int, default=0)
    p.add_argument("--cost", type=float, default=0)
    p.add_argument("--latency-ms", type=int)
    p.add_argument("--task-type")
    p.add_argument("--skill")
    p.add_argument("--agent")
    p = sub.add_parser("inference-stats", help="Inference stats")
    p.add_argument("--tenant-id")
    p.add_argument("--days", type=int, default=30)
    p = sub.add_parser("list-inference", help="List inference logs")
    p.add_argument("--tenant-id")
    p.add_argument("--limit", type=int, default=100)
    
    # files
    p = sub.add_parser("register-file", help="Register a workspace file")
    p.add_argument("--tenant-id")
    p.add_argument("--project-id")
    p.add_argument("--doc-id", dest="document_id")
    p.add_argument("--file-path", required=True)
    p.add_argument("--file-type", required=True)
    p.add_argument("--created-by", default="manual")
    p.add_argument("--purpose")
    p = sub.add_parser("list-files", help="List workspace files")
    p.add_argument("--tenant-id")
    p.add_argument("--project-id")
    p.add_argument("--file-type")
    
    # agent sessions
    p = sub.add_parser("start-session", help="Start agent session")
    p.add_argument("--tenant-id")
    p.add_argument("--parent-session")
    p.add_argument("--agent-name", required=True)
    p.add_argument("--skill-id")
    p.add_argument("--task")
    p = sub.add_parser("complete-session", help="Complete agent session")
    p.add_argument("session_id")
    p.add_argument("--status", default="done")
    p.add_argument("--result")
    p.add_argument("--error")
    p = sub.add_parser("list-sessions", help="List agent sessions")
    p.add_argument("--tenant-id")
    p.add_argument("--parent-session")
    
    # api keys
    p = sub.add_parser("create-key", help="Create API key")
    p.add_argument("tenant_id")
    p.add_argument("--name")
    p = sub.add_parser("verify-key", help="Verify API key")
    p.add_argument("key")
    p = sub.add_parser("list-keys", help="List API keys")
    p.add_argument("tenant_id")
    
    # stats
    sub.add_parser("stats", help="Show stats")
    p = sub.add_parser("stats-for", help="Stats for tenant")
    p.add_argument("tenant_id")
    
    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return
    
    # Execute commands
    if args.cmd == "init":
        init_db()
    
    elif args.cmd == "list-tenants":
        print(json.dumps(list_tenants(), indent=2, default=str))
    
    elif args.cmd == "create-tenant":
        print(json.dumps(create_tenant(args.name), indent=2))
    
    elif args.cmd == "create-project":
        settings = json.loads(args.settings) if args.settings else None
        print(json.dumps(create_project(args.tenant_id, args.name, args.description, settings), indent=2))
    
    elif args.cmd == "list-projects":
        print(json.dumps(list_projects(args.tenant_id), indent=2, default=str))
    
    elif args.cmd == "get-project":
        print(json.dumps(get_project(args.project_id), indent=2, default=str))
    
    elif args.cmd == "update-project-settings":
        settings = json.loads(args.settings) if args.settings else {}
        print(json.dumps(update_project_settings(args.project_id, settings), indent=2))
    
    elif args.cmd == "add-doc":
        print(json.dumps(add_document(args.project_id, args.file_path, args.tier), indent=2))
    
    elif args.cmd == "list-docs":
        print(json.dumps(list_documents(args.project_id), indent=2, default=str))
    
    elif args.cmd == "get-doc":
        print(json.dumps(get_document(args.doc_id), indent=2, default=str))
    
    elif args.cmd == "delete-doc":
        print(json.dumps(delete_document(args.doc_id, args.hard), indent=2))
    
    elif args.cmd == "register-skill":
        print(json.dumps(register_skill(
            args.tenant_id, args.name, args.file_path, args.desc,
            args.category, args.tags, args.created_by
        ), indent=2))
    
    elif args.cmd == "list-skills":
        print(json.dumps(list_skills(args.tenant_id, args.category), indent=2, default=str))
    
    elif args.cmd == "get-skill":
        print(json.dumps(get_skill(args.skill_id), indent=2, default=str))
    
    elif args.cmd == "log-inference":
        print(json.dumps(log_inference(
            args.tenant_id, args.provider, args.model,
            args.prompt_tokens, args.completion_tokens, args.cost,
            args.latency_ms, args.task_type, args.skill, args.agent
        ), indent=2))
    
    elif args.cmd == "inference-stats":
        print(json.dumps(get_inference_stats(args.tenant_id, args.days), indent=2, default=str))
    
    elif args.cmd == "list-inference":
        print(json.dumps(get_inference_logs(args.tenant_id, args.limit), indent=2, default=str))
    
    elif args.cmd == "register-file":
        print(json.dumps(register_file(
            args.tenant_id, args.project_id, args.document_id,
            args.file_path, None, args.file_type, args.created_by, args.purpose
        ), indent=2))
    
    elif args.cmd == "list-files":
        print(json.dumps(list_files(args.tenant_id, args.project_id, args.file_type), indent=2, default=str))
    
    elif args.cmd == "start-session":
        print(json.dumps(start_agent_session(
            args.tenant_id, args.parent_session, args.agent_name,
            args.skill_id, args.task
        ), indent=2))
    
    elif args.cmd == "complete-session":
        print(json.dumps(complete_agent_session(
            args.session_id, args.result, args.error, args.status
        ), indent=2))
    
    elif args.cmd == "list-sessions":
        print(json.dumps(get_agent_sessions(args.parent_session, args.tenant_id), indent=2, default=str))
    
    elif args.cmd == "create-key":
        print(json.dumps(create_api_key(args.tenant_id, args.name), indent=2))
    
    elif args.cmd == "verify-key":
        result = verify_api_key(args.key)
        print(json.dumps(result, indent=2, default=str) if result else '{"valid": false}')
    
    elif args.cmd == "list-keys":
        print(json.dumps(list_api_keys(args.tenant_id), indent=2, default=str))
    
    elif args.cmd == "stats":
        print(json.dumps(get_stats(), indent=2))
    
    elif args.cmd == "stats-for":
        print(json.dumps(get_stats(args.tenant_id), indent=2))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
