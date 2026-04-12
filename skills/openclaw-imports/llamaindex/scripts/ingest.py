#!/usr/bin/env python3
"""
LlamaIndex Document Ingestion Pipeline
Usage: python ingest.py ./documents --client "acme-corp" --storage ./chroma_db
"""

import argparse
import sys
from pathlib import Path

from llama_index.readers.file import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
import chromadb


def parse_args():
    parser = argparse.ArgumentParser(description="Ingest documents with LlamaIndex")
    parser.add_argument("input_dir", type=str, help="Directory containing documents")
    parser.add_argument("--client", type=str, default=None, help="Client name for metadata")
    parser.add_argument("--storage", type=str, default="./chroma_db", help="Chroma DB path")
    parser.add_argument("--chunk-size", type=int, default=512, help="Chunk size")
    parser.add_argument("--chunk-overlap", type=int, default=50, help="Chunk overlap")
    parser.add_argument("--embed-model", type=str, default="local:BAAI/bge-small-en-v1.5", 
                        help="Embedding model")
    return parser.parse_args()


def main():
    args = parse_args()
    input_path = Path(args.input_dir)
    
    if not input_path.exists():
        print(f"Error: {args.input_dir} does not exist")
        sys.exit(1)
    
    print(f"Loading documents from {args.input_dir}...")
    
    # Load documents
    reader = SimpleDirectoryReader(
        input_dir=str(input_path),
        recursive=True,
        metadata_fn=lambda f: {
            "file_name": Path(f).name,
            "client": args.client,
        } if args.client else {"file_name": Path(f).name}
    )
    documents = reader.load_data()
    print(f"Loaded {len(documents)} documents")
    
    # Parse into chunks
    splitter = SentenceSplitter(chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap)
    nodes = splitter.get_nodes_from_documents(documents)
    print(f"Created {len(nodes)} nodes")
    
    # Setup vector store
    chroma_client = chromadb.PersistentClient(path=args.storage)
    collection = chroma_client.get_or_create_collection("documents")
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    # Build index
    print("Building index...")
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        embed_model=args.embed_model,
        show_progress=True,
    )
    
    print(f"Index built successfully with {len(index.docstore)} documents")
    print(f"Storage: {args.storage}")


if __name__ == "__main__":
    main()
