#!/usr/bin/env python3
"""
Query a LlamaIndex vector store (retrieval only, no LLM needed)
Usage: python query.py "What are the payment terms?" --storage ./chroma_db
"""

import argparse
import sys

from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex
import chromadb


def parse_args():
    parser = argparse.ArgumentParser(description="Query indexed documents")
    parser.add_argument("query", type=str, help="Query string")
    parser.add_argument("--storage", type=str, default="./chroma_db", help="Chroma DB path")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Load vector store
    chroma_client = chromadb.PersistentClient(path=args.storage)
    collection = chroma_client.get_or_create_collection("documents")
    vector_store = ChromaVectorStore(chroma_collection=collection)
    
    # Build index (local embedding model)
    index = VectorStoreIndex.from_vector_store(
        vector_store,
        embed_model="local:BAAI/bge-small-en-v1.5"
    )
    
    # Retrieve results directly (no LLM needed)
    retriever = index.as_retriever(similarity_top_k=args.top_k)
    nodes = retriever.retrieve(args.query)
    
    print(f"\nQuery: {args.query}")
    print(f"\nTop {len(nodes)} results:\n")
    
    for i, node in enumerate(nodes, 1):
        score = node.score if hasattr(node, 'score') else 'N/A'
        print(f"[{i}] Score: {score:.3f}")
        print(f"    Source: {node.metadata.get('file_name', 'Unknown')}, Page {node.metadata.get('page_number', 'N/A')}")
        print(f"    Text: {node.text[:300]}...")
        print()


if __name__ == "__main__":
    main()
