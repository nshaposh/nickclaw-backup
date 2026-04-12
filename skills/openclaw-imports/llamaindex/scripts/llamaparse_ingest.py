#!/usr/bin/env python3
"""
LlamaParse Document Ingestion Pipeline with DB tracking
Usage: python llamaparse_ingest.py ./document.pdf --project-id proj_xxx --api-key "llx-..."

Requires: db_manager.py in the same directory
"""

import argparse
import asyncio
import json
import sys
import traceback
from pathlib import Path

from llama_cloud import AsyncLlamaCloud
import chromadb
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext, VectorStoreIndex, Document

# Import DB helpers from db_manager
sys.path.insert(0, str(Path(__file__).parent))
from db_manager import add_document, update_document_status, add_chunks, get_project_settings


def init_db():
    """Ensure database is initialized."""
    db_path = Path(__file__).parent.parent / "data" / "documents.db"
    if not db_path.exists():
        from db_manager import init_db as _init
        _init()


def update_status(doc_id: str, status: str, **kwargs):
    """Update document status in DB."""
    try:
        update_document_status(doc_id, parse_status=status, **kwargs)
    except Exception as e:
        print(f"[DB] Warning: could not update status: {e}")


async def parse_with_llamaparse(client: AsyncLlamaCloud, file_path: str, args) -> tuple:
    """Parse document using LlamaParse. Returns (documents, total_pages)."""
    print(f"Uploading {file_path} to LlamaParse...")
    
    file_obj = await client.files.create(file=file_path, purpose="parse")
    
    print(f"Parsing (tier={args.tier})...")
    result = await client.parsing.parse(
        file_id=file_obj.id,
        tier=args.tier,
        version="latest",
        output_options={
            "markdown": {"tables": {"output_tables_as_markdown": args.tables_as_markdown}},
            "images_to_save": ["screenshot"] if args.extract_images else [],
        },
        processing_options={
            "ignore": {"ignore_diagonal_text": args.ignore_diagonal},
            "ocr_parameters": {"languages": args.languages.split(",") if args.languages else ["en"]},
        },
        expand=["text", "markdown", "items"],
    )
    
    documents = []
    for page in result.markdown.pages:
        if page.markdown.strip():
            doc = Document(
                text=page.markdown,
                metadata={
                    "source": Path(file_path).name,
                    "page_number": page.page_number,
                    "total_pages": len(result.markdown.pages),
                    "parser": "llamaparse",
                    "tier": args.tier,
                }
            )
            documents.append(doc)
    
    return documents, len(result.markdown.pages)


async def main():
    parser = argparse.ArgumentParser(description="Ingest documents with LlamaParse + DB tracking")
    parser.add_argument("file", type=str, help="Path to document (PDF, DOCX, etc.)")
    parser.add_argument("--project-id", type=str, required=True,
                        help="Project ID from database (e.g., proj_xxx)")
    parser.add_argument("--api-key", type=str, default=None, help="LlamaCloud API key")
    parser.add_argument("--output", type=str, default="./parsed", help="Output directory for markdown")
    parser.add_argument("--storage", type=str, default=None,
                        help="Chroma DB path (default: ./chroma_db)")
    parser.add_argument("--tier", type=str, default="agentic", choices=["fast", "cost_effective", "agentic", "agentic_plus"])
    parser.add_argument("--chunk-size", type=int, default=512, help="Chunk size")
    parser.add_argument("--chunk-overlap", type=int, default=50, help="Chunk overlap")
    parser.add_argument("--embed-model", type=str, default="local:BAAI/bge-small-en-v1.5")
    parser.add_argument("--tables-as-markdown", action="store_true", default=True)
    parser.add_argument("--ignore-diagonal", action="store_true", default=True)
    parser.add_argument("--languages", type=str, default="en")
    parser.add_argument("--extract-images", action="store_true")
    parser.add_argument("--save-markdown", action="store_true")
    parser.add_argument("--skip-db", action="store_true", help="Skip DB tracking (standalone mode)")
    
    args = parser.parse_args()
    
    # --- Load project settings (defaults override by CLI args) ---
    project_settings = {}
    if not args.skip_db:
        try:
            init_db()
            project_settings = get_project_settings(args.project_id)
            print(f"[DB] Loaded project settings: embed_model={project_settings.get('embed_model')}")
        except Exception as e:
            print(f"[DB] Warning: could not load project settings: {e}")
    
    # Apply project defaults (CLI args take precedence over project settings)
    if args.skip_db or not project_settings:
        # In skip-db mode or no DB, use CLI defaults
        args.tier = args.tier or "agentic"
        args.embed_model = args.embed_model or "local:BAAI/bge-small-en-v1.5"
    else:
        # Project settings override CLI defaults (but not explicit CLI args)
        if args.tier == "agentic":  # still at default, apply project setting
            args.tier = project_settings.get("parse_tier", "agentic")
        if args.embed_model == "local:BAAI/bge-small-en-v1.5":
            args.embed_model = project_settings.get("embed_model", "local:BAAI/bge-small-en-v1.5")
        if args.chunk_size == 512:
            args.chunk_size = project_settings.get("chunk_size", 512)
        if args.chunk_overlap == 50:
            args.chunk_overlap = project_settings.get("chunk_overlap", 50)
    
    # Defaults
    if not args.storage:
        args.storage = f"./chroma_{args.project_id}"
    
    doc_id = None
    
    # --- DB: Add document record ---
    if not args.skip_db:
        try:
            result = add_document(
                project_id=args.project_id,
                file_path=args.file,
                parse_tier=args.tier,
                parse_status="parsing"
            )
            if "error" in result:
                print(f"[DB] {result['error']}: {result.get('existing_id')}")
                if "already exists" in result.get('error', ''):
                    sys.exit(0)
            else:
                doc_id = result["id"]
                print(f"[DB] Created document: {doc_id}")
                update_status(doc_id, "parsing")
        except Exception as e:
            print(f"[DB] Warning: could not create document record: {e}")
            args.skip_db = True
    
    # --- Get API key ---
    api_key = args.api_key
    if not api_key:
        key_path = Path("/root/.openclaw/config/llamaparse.key")
        if key_path.exists():
            api_key = key_path.read_text().strip()
    if not api_key:
        print("Error: LlamaCloud API key required. Set --api-key or /root/.openclaw/config/llamaparse.key")
        if doc_id:
            update_status(doc_id, "failed", parse_error="No API key")
        sys.exit(1)
    
    try:
        # --- Parse ---
        client = AsyncLlamaCloud(api_key=api_key)
        documents, total_pages = await parse_with_llamaparse(client, args.file, args)
        print(f"Parsed {len(documents)} pages")
        
        if not args.skip_db and doc_id:
            update_status(doc_id, "parsing",
                         pages_parsed=len(documents),
                         parsed_markdown_path=str(Path(args.output).absolute()))
        
        # --- Save markdown ---
        if args.save_markdown:
            output_path = Path(args.output)
            output_path.mkdir(parents=True, exist_ok=True)
            base_name = Path(args.file).stem
            for doc in documents:
                page_num = doc.metadata["page_number"]
                out_file = output_path / f"{base_name}_page_{page_num}.md"
                out_file.write_text(doc.text)
            print(f"Saved markdown to {output_path}")
        
        # --- Chunk ---
        splitter = SentenceSplitter(chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap)
        nodes = splitter.get_nodes_from_documents(documents)
        print(f"Created {len(nodes)} nodes")
        
        # --- Chroma ---
        chroma_path = args.storage
        chroma_client = chromadb.PersistentClient(path=chroma_path)
        collection_name = f"proj_{args.project_id.replace('proj_', '')}"
        collection = chroma_client.get_or_create_collection(collection_name)
        vector_store = ChromaVectorStore(chroma_collection=collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # --- Build index ---
        print("Building index...")
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            embed_model=args.embed_model,
            show_progress=True,
        )
        
        # --- DB: Store chunks ---
        if not args.skip_db and doc_id:
            chunks_data = []
            for i, node in enumerate(nodes):
                chunks_data.append({
                    "chunk_index": i,
                    "text": node.text,
                    "char_count": len(node.text),
                    "page_number": node.metadata.get("page_number"),
                    "chroma_id": node.id_
                })
            try:
                add_chunks(doc_id, chunks_data)
                print(f"[DB] Stored {len(chunks_data)} chunks")
            except Exception as e:
                print(f"[DB] Warning: could not store chunks: {e}")
        
        # --- Done ---
        if not args.skip_db and doc_id:
            update_status(doc_id, "done",
                         index_status="done",
                         chunks_indexed=len(nodes),
                         chroma_collection=collection_name)
        
        print(f"✅ Index built with {len(nodes)} nodes indexed")
        print(f"Storage: {chroma_path}")
        print(f"Collection: {collection_name}")
        
    except Exception as e:
        error_msg = traceback.format_exc()
        print(f"❌ Error: {e}")
        if doc_id:
            update_status(doc_id, "failed", parse_error=str(e)[:500])
        sys.exit(1)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
