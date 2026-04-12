---
name: llamaindex
description: Use LlamaIndex for document ingestion, parsing, vectorization, and RAG pipelines. Triggers on requests like "parse a document", "load documents", "build a RAG pipeline", "index documents for retrieval", "set up a vector store", "query indexed documents", "ingest documents". Covers PDF, DOCX, TXT, HTML, Markdown parsing with LlamaParse (preferred) and SimpleDirectoryReader, vector storage with Chroma/FAISS, and query engine construction.
---

# LlamaIndex - Document Processing & RAG

## Quick Setup

```bash
pip install llama-index llama-index-readers-file llama-index-vector-stores-chroma llama-index-embeddings-openai llama_cloud>=1.0.0
```

## Core Workflow

### 1. Parse Documents with LlamaParse (Preferred)

LlamaParse produces structured Markdown from complex documents (PDFs, Office files, images).

```python
from llama_cloud import AsyncLlamaCloud
import httpx

client = AsyncLlamaCloud(api_key="llx-...")  # Get from app.llamaparser.ai

# Upload and parse
file_obj = await client.files.create(file="./document.pdf", purpose="parse")

result = await client.parsing.parse(
    file_id=file_obj.id,
    tier="agentic",           # or "standard"
    version="latest",
    output_options={
        "markdown": {"tables": {"output_tables_as_markdown": False}},
        "images_to_save": ["screenshot"],
    },
    processing_options={
        "ignore": {"ignore_diagonal_text": True},
        "ocr_parameters": {"languages": ["en"]}  # specify language
    },
    expand=["text", "markdown", "items", "images_content_metadata"],
)

# Get markdown content
for page in result.markdown.pages:
    print(page.markdown)
```

### 2. Fallback: SimpleDirectoryReader

For simpler documents or when LlamaParse isn't needed:

```python
from llama_index.readers.file import SimpleDirectoryReader
documents = SimpleDirectoryReader("./documents").load_data()
```

### 3. Chunking

```python
from llama_index.core.node_parser import SentenceSplitter

splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
nodes = splitter.get_nodes_from_documents(documents)
```

**Chunking strategies by doc type:**
- **Contracts/Legal**: Larger chunks (1024), overlap (128)
- **Policies/Manuals**: Medium (768), overlap (64)
- **Notes/Emails**: Smaller (256), overlap (32)

### 4. Vectorize & Store

```python
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
import chromadb

chroma_client = chromadb.PersistClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection("documents")
vector_store = ChromaVectorStore(chroma_collection=collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)
```

### 5. Build Index

```python
from llama_index.core import VectorStoreIndex

index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
    embed_model="local:BAAI/bge-small-en-v1.5"  # or OpenAIEmbeddings()
)
```

### 6. Query

```python
query_engine = index.as_query_engine(similarity_top_k=5)
response = query_engine.query("What are the payment terms?")
print(response.source_nodes)  # citations with sources
```

## LlamaParse vs SimpleDirectoryReader

| Feature | LlamaParse | SimpleDirectoryReader |
|---------|-----------|----------------------|
| PDF layout preservation | ✅ | ❌ |
| Table extraction | ✅ (structured) | ❌ (raw) |
| Image extraction | ✅ | Limited |
| OCR | ✅ | ❌ |
| Markdown output | ✅ | ❌ |
| Cost | API-based | Free |
| Use case | Complex docs, production | Simple docs, dev |

**Recommendation:** Use LlamaParse for:
- Scanned PDFs
- Complex layouts (multi-column, tables)
- Image-heavy documents
- Any document where structure matters

## Directory Structure

```
/documents
  /clients
    /{client-name}
      /raw          # original files
      /parsed       # LlamaParse markdown output
      /indexed      # vector store
  /knowledge-base
    /{topic}
```

## RAG Pipeline Best Practices

1. **Use LlamaParse** for complex documents to preserve structure
2. **Hybrid search** (dense + sparse) outperforms vector similarity alone
3. **Re-ranking** with CrossEncoder for better top-k results
4. **Citation tracking** — always expose source nodes to user
5. **Metadata filtering** — filter by client, date, doc type

## Scripts

- `scripts/llamaparse_ingest.py` — LlamaParse ingestion pipeline
- `scripts/ingest.py` — SimpleDirectoryReader fallback pipeline
- `scripts/query.py` — Query the vector store

## References

- `references/concepts.md` — LlamaIndex core concepts
- `references/storage.md` — Storage backend options (Chroma, FAISS, Qdrant)
- `references/chunking.md` — Chunking strategies by document type
