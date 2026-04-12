---
name: falkordb-quickstart
description: Quick-start guide for FalkorDB graph database — connection, Python client, Cypher queries, and browser UI
category: data-science
---

# FalkorDB Quick-Start

Quick-start guide for FalkorDB — a graph database built on Redis.

## Connection Details

### Docker Setup
FalkorDB runs as a Docker container with Redis as the backend:
```
docker run -d --name falkordb -p 3000:3000 -p 6379:6379 falkordb/falkordb
```
- Port **3000** = Browser UI (no auth by default)
- Port **6379** = Redis/FalkorDB protocol (may require auth)

### Host/Port for Clients
From the **host machine** (outside Docker):
- Browser UI: `http://localhost:3000` (no password)
- Python client: `172.17.0.1:6379` (Docker bridge gateway) — NOT `localhost`

The Docker bridge gateway IP (`172.17.0.1`) is the key — it routes to the internal Redis port from the host. From inside the Docker network, use `localhost`.

### Auth
- Default Redis `requirepass` is `FalkorDB2026!` (set in the container's redis.conf)
- Browser UI: leave username blank, use password `FalkorDB2026!`
- Python client: `FalkorDB(host="172.17.0.1", port=6379, password="FalkorDB2026!")`
- Docker bridge (`172.17.0.1`) has no auth — use for local development only

### Existing Graphs
```
redis-cli -h 172.17.0.1 -p 6379 --no-auth-warning KEYS '*'
```

## Python Client (falkordb)

```python
from falkordb import FalkorDB, Graph, Node, Edge

db = FalkorDB(host="172.17.0.1", port=6379, password="FalkorDB2026!")
graph = db.select_graph("mygraph")

# List existing graphs
db.list_graphs()

# Delete a graph
db.delete_graph("mygraph")
```

## Node and Edge API

### Node properties
Node properties use **lowercase keys** in the Python API:
```python
node = Node(
    alias="n_1",
    labels="actor",
    properties={'name': 'Tom Hanks', 'age': 67}  # lowercase keys!
)
```

### CSV import gotcha
The IMDB demo's `actors.csv` has column `birthYear`, but the demo script references `yearOfBirth` — a column that doesn't exist. Fix by computing derived fields explicitly:
```python
age = 2019 - yearOfBirth  # compute age from birthYear
```

### Fulltext Index
`graph.create_node_fulltext_index()` **does not exist** in the current client. Use Cypher:
```python
graph.query("CREATE FULLTEXT INDEX FOR (n:actor) ON EACH [n.name]")
```

### Edge API
```python
edge = Edge(source_node, "REL_TYPE", target_node)
```

## Cypher Queries

### Basic patterns
```cypher
MATCH (a:actor)-[:act]->(m:movie) RETURN a.name, m.title LIMIT 10
MATCH (a:actor {name: 'Tom Hanks'})-[:act]->(m:movie) RETURN m.title, m.rating ORDER BY m.rating DESC
MATCH (m:movie)<-[:act]-(a:actor) WHERE m.genre = 'Action' AND m.year > 2010 RETURN a.name, count(m) as mc ORDER BY mc DESC LIMIT 10
```

### Aggregations
```cypher
MATCH (m:movie)<-[:act]-(a:actor)
WITH m, count(a) as actor_count, m.rating as rating, m.title as title
RETURN title, rating, actor_count ORDER BY rating DESC LIMIT 10

MATCH (m:movie)
WITH m.genre as genre, max(m.rating) as max_rating
MATCH (m2:movie)
WHERE m2.genre = genre AND m2.rating = max_rating
RETURN genre, m2.title, max_rating
```

## Browser UI Tips

- Log in at `http://localhost:3000` with Host: `172.17.0.1`, Password: `FalkorDB2026!`
- After login: click **GRAPHS** → select your graph
- Click **Skip Tutorial** immediately on first load to dismiss the 27-step tour
- Click label buttons (e.g., "actor", "movie") in the Labels panel to render nodes in the graph canvas
- Click **All labels** (*) to render all node types at once (slow for large graphs)
- The **Table** tab shows query results in tabular format; **Graph** tab shows network visualization

## Demo Data

The IMDB demo at `https://github.com/FalkorDB/FalkorDB` includes:
- `demos/imdb/` — CSV files: `movies.csv` and `actors.csv`
- `demos/imdb/demo.py` — Python loader script (has bugs — fix column name mismatch manually)

Stats for loaded IMDB data: 1,317 actors, 283 movies, 1,839 `act` relationships
