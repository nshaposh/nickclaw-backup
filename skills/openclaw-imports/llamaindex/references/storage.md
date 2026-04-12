# Vector Storage Backends

## Chroma (Recommended for Most Cases)

**Pros:** Easy to use, embedded mode, good for single-node setups
**Cons:** Not distributed, limited scalability

```python
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

chroma_client = chromadb.PersistClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection("documents")
vector_store = ChromaVectorStore(chroma_collection=collection)
```

## FAISS (Facebook AI Similarity Search)

**Pros:** Fast, efficient, good for large datasets
**Cons:** No metadata filtering out of box, in-memory only

```python
from llama_index.vector_stores.faiss import FAISSVectorStore
from llama_index.core import StorageContext

# Index must be built first, then save/load
faiss_store = FAISSVectorStore.from_documents(documents, embed_model)
faiss_store.save("faiss_index")
loaded_store = FAISSVectorStore.load("faiss_index")
```

## Qdrant (Production-Ready)

**Pros:** Distributed, metadata filtering, cloud offering
**Cons:** Requires running Qdrant service

```python
from llama_index.vector_stores.qdrant import QdrantVectorStore

vector_store = QdrantVectorStore(
    host="localhost",
    collection_name="documents",
)
```

## Weaviate

**Pros:** Graph-based, semantic caching
**Cons:** More complex setup

```python
from llama_index.vector_stores.weaviate import WeaviateVectorStore

vector_store = WeaviateVectorStore(
    weaviate_url="http://localhost:8080",
    index_name="Documents",
)
```

## Choosing a Backend

| Use Case | Recommendation |
|----------|---------------|
| Solo/Dev | Chroma (embedded) |
| Small Biz | Chroma or Qdrant (cloud) |
| Enterprise | Qdrant or Weaviate |
| Huge Scale | Qdrant (distributed) |
