---
name: neo4j-http-api
description: Access Neo4j via HTTP REST API from Python without the slow/blocked Bolt driver
---

# Neo4j HTTP API — Python Access Without the Driver

## When to Use

The official `neo4j` Python driver can be slow or blocked in certain environments:
- Hermes terminal commands (often blocked/timed out)
- Cloud sandboxes with restricted network policies
- Environments where the Bolt protocol (7687) is filtered

**Workaround:** Use the Neo4j HTTP REST API on port 7474 instead. It supports all Cypher queries and is significantly faster in these environments.

## Connection

```python
import requests

auth = ("neo4j", "password")
base = "http://localhost:7474/db/neo4j/query/v2"

def cypher(query, params=None):
    payload = {"statement": query}
    if params:
        payload["params"] = params
    r = requests.post(base, auth=auth, json=payload, timeout=10)
    data = r.json()["data"]
    cols = data.get("fields", [])
    return [dict(zip(cols, row)) for row in data["values"]]
```

## Key Endpoints

| Endpoint | Purpose |
|---|---|
| `POST /db/neo4j/query/v2` | Execute Cypher query |
| `GET /db/neo4j/schema` | Get schema (labels, relationship types) |
| `GET /db/neo4j` | Server info, version |

## Named Results

For results as dicts (with column names):

```python
def cypher_named(query):
    r = requests.post(base, auth=auth, json={"statement": query}, timeout=10)
    data = r.json()["data"]
    cols = data.get("fields", [])
    return [dict(zip(cols, row)) for row in data["values"]]

# Usage
results = cypher_named("MATCH (e:Employee) RETURN e.name as name, e.role as role")
for row in results:
    print(row["name"], row["role"])
```

## Gotcha

Authentication: uses HTTP Basic Auth, not Bolt credentials. Format is:
```python
auth = ("neo4j", "your_password")  # same as browser login
```

## Verified Working

- Neo4j 2026.03.1 (Docker latest) — works
- Python `requests` library — reliable
- Hermes `execute_code` sandbox — fast (~1s per query)
- Hermes `terminal()` — slow or blocked for neo4j driver, but HTTP API works

## Schema Discovery

```python
labels = cypher("CALL db.labels()")           # → [{'label': 'Employee'}, ...]
rel_types = cypher("CALL db.relationshipTypes()")  # → [{'relationshipType': 'KNOWS'}, ...]
```
