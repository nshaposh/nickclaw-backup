---
name: wiki-domain-discovery
description: Process for discovering and mapping the domain and structure of a project-specific wiki when the exact path is unknown or ambiguous.
---

# Wiki Domain Discovery

When a user asks about the "domains", "topics", or "content" of a wiki, and the exact location is uncertain or has shifted (e.g., `/wiki` vs `/wiki/l`), follow this discovery pipeline to ensure accuracy and avoid confirmation bias.

## Steps

1. **Global Schema Search**: 
   Instead of guessing paths, search for the `SCHEMA.md` file. This is the "source of truth" for the wiki's domain, taxonomy, and organization rules.
   - Command: `find /home -name "SCHEMA.md" 2>/dev/null`

2. **Identify the Root**: 
   Once `SCHEMA.md` is found, identify the parent directory as the Wiki Root. Do not assume any further subdirectories (like `/l/`) unless explicitly verified.

3. **Read Domain Definition**: 
   Read the `SCHEMA.md` file to identify the explicit "Domain" section. This tells you exactly what the wiki is intended to cover.

4. **Map the Content**: 
   Read `index.md` to see the actual population of pages (Entities, Concepts, etc.). This confirms if the *intended* domain matches the *actual* content.

5. **Surface Relationships**: 
   To represent the wiki as a "graph" or "map", read the individual pages for `[[wikilinks]]`. This allows you to identify the "Hub" nodes (pages most linked to) and "Gaps" (referenced pages that don't exist yet).

## Pitfalls
- **Confirmation Bias**: Do not trust a path provided in the chat history if it previously failed. Always verify with a filesystem search.
- **Index vs. Schema**: `index.md` tells you what is *there*; `SCHEMA.md` tells you what *should* be there. Use both to provide a complete answer.

## Verification
- Does the reported domain match the `SCHEMA.md` definition?
- Are the linked pages listed in the `index.md`?
- Has the correct root path been saved to memory to prevent future "wrong place" errors?
