# LlamaIndex Core Concepts

## Documents vs Nodes

- **Document**: Represents a full file (PDF, DOCX, etc.)
- **Node**: A chunk/segment of a document after parsing

## Index Types

| Index | Use Case |
|-------|----------|
| VectorStoreIndex | Semantic search, RAG |
| SummaryIndex | Summarization, list-based queries |
| TreeIndex | Hierarchical summaries |
| KeywordTableIndex | Keyword-based retrieval |

## Storage Components

- **Docstore**: Stores Node objects (raw text + metadata)
- **IndexStore**: Stores index metadata
- **VectorStore**: Stores embeddings

## Embedding Models

```python
# OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
embed = OpenAIEmbedding(model="text-embedding-ada-002")

# Local (BGE - recommended)
embed = "local:BAAI/bge-small-en-v1.5"

# Local (MiniLM)
embed = "local:sentence-transformers/all-MiniLM-L6-v2"
```

## Query Engines

```python
# Simple query
query_engine = index.as_query_engine()

# With filters
query_engine = index.as_query_engine(
    similarity_top_k=5,
    vector_store_query_mode="hybrid"  # dense + sparse
)

# With re-ranking
from llama_index.postprocessor.cohere_rerank import CohereRerank
postprocessor = CohereRerank(api_key=..., top_n=3)
query_engine = index.as_query_engine(
    similarity_top_k=10,
    node_postprocessors=[postprocessor]
)
```

## Response Modes

```python
# Compact (default) - combines relevant chunks
query_engine = index.as_query_engine(response_mode="compact")

# Refine - iterates through chunks
query_engine = index.as_query_engine(response_mode="refine")

# Tree summarize - good for summary queries
query_engine = index.as_query_engine(response_mode="tree_summarize")
```
