# Chunking Strategies by Document Type

## Principles

1. **Bigger context ≠ better** — Relevant chunks beat large chunks
2. **Overlap helps** — 10-20% overlap prevents cutting context mid-thought
3. **Respect structure** — Split on headers, paragraphs, not sentences mid-thought

## By Document Type

### Contracts / Legal Documents
```
chunk_size: 1024-2048
chunk_overlap: 128-256
```
- Preserve legal clause integrity
- Larger chunks maintain context
- Low overlap (clauses are self-contained)

### Policies / Employee Manuals
```
chunk_size: 768-1024
chunk_overlap: 64-128
```
- Medium chunks for procedure steps
- Overlap to catch cross-references

### Reports / Financial Documents
```
chunk_size: 512-768
chunk_overlap: 64
```
- Tables and figures need smaller context
- Section-based chunking preferred

### Emails / Short Communications
```
chunk_size: 256-512
chunk_overlap: 32
```
- Already small, minimal chunking
- Include metadata (sender, date)

### Knowledge Base / FAQs
```
chunk_size: 256-512
chunk_overlap: 32
```
- Q&A pairs are naturally small
- Each Q&A = one chunk

## Semantic Chunking

For more intelligent splitting:

```python
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.embeddings.openai import OpenAIEmbedding

splitter = SemanticSplitterNodeParser(
    embed_model=OpenAIEmbedding(),
    buffer_size=1,  # sentences to consider
    breakpoint_percentile_threshold=95,  # split threshold
)
```

## Metadata to Preserve

Always include:
- `file_name`
- `file_type`
- `client` / `project`
- `date` / `year`

Optionally:
- `section`
- `author`
- `page_number`
