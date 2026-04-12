---
name: project-management
description: Lightweight multi-project tracking system for Nick's work
---

# Project Management System

## Overview
Nick manages multiple simultaneous projects. A lightweight flat-file system tracks all workstreams.

## Directory Structure
```
projects/
  PROJECTS.md              # Master registry: all projects, status, next action
  ai-agents-business/      # One folder per project
    PROJECT.md             # What it is, goals, status
    TASKS.md               # Open / done / blocked tasks
    DATA/                  # Datasets, outputs, files
    NOTES/                 # Research, docs, findings
  census-analysis/
    ...
```

## Files

### PROJECTS.md
```markdown
# Projects Registry

## 1. Project Name — Status (started YYYY-MM-DD)
Next action: ...

## 2. Project Name — Status (started YYYY-MM-DD)
Next action: ...
```

### PROJECT.md
```markdown
# [Project Name]

**Status:** 🟡 In Progress
**Started:** YYYY-MM-DD
**Client/For:** ...

## Goals
- ...

## Status Notes
...
```

### TASKS.md
```markdown
# Tasks

## 🔴 Blocked
- ...

## 🟡 In Progress
- ...

## ✅ Done
- ...
```

## Workflow

1. **New project**: create folder, PROJECT.md, TASKS.md, register in PROJECTS.md
2. **Session start**: read PROJECTS.md to know what's in flight
3. **Task done**: move from In Progress → Done in TASKS.md
4. **Blocked task**: move to Blocked with reason noted
5. **Project done**: update status in PROJECTS.md and PROJECT.md

## Status Icons
- 🟡 Planning
- 🟢 Active
- 🔴 Blocked
- ✅ Done
