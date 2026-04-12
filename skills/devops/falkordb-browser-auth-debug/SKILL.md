---
name: falkordb-browser-auth-debug
description: Debug 500 errors in FalkorDB Browser when Redis requirepass is set
category: devops
tags: [falkordb, redis, graphdb, nextauth, docker]
---

# FalkorDB Browser — Auth & 500 Error Debugging

## Context
FalkorDB Browser (port 3000) is a Next.js app embedded in the FalkorDB docker container. When Redis `requirepass` is set, the browser starts returning 500 errors.

## Root Cause
The browser uses **NextAuth with Redis as its session/user store** (not env-file credentials). When `requirepass` is set on Redis but the browser's connection string doesn't include it, Redis rejects the connection → 500 error.

User credentials (username/password) are stored as keys in Redis itself, not in `.env.local`. The default login is username `Default`, password `Default` (blank).

## Debugging Steps

### 1. Inspect the browser's env
```bash
docker exec falkordb cat /var/lib/falkordb/browser/.env.local
```
Key vars: `NEXTAUTH_URL`, `NEXTAUTH_SECRET`, `ALLOWED_ORIGINS`, `ENCRYPTION_KEY`

### 2. Check if Redis auth broke the browser
```bash
docker exec falkordb redis-cli ping  # returns "NOAUTH" if auth is required
```

### 3. Set a Redis password (if not already set)
```bash
docker exec falkordb redis-cli CONFIG SET requirepass "YourPassword!"
```

### 4. Fix: reconnect with password in the login form
Navigate to `http://<host>:3000`, use the login form with the new Redis password. The browser stores the updated credentials in Redis on successful login.

### 5. Fix CORS for remote access
The browser's CORS is locked to `localhost:3000` by default. Update it:
```bash
docker exec falkordb sh -c 'echo "ALLOWED_ORIGINS=http://your-actual-origin:3000" >> /var/lib/falkordb/browser/.env.local'
docker restart falkordb
```

## Key Insight
**The browser login form specifies the Redis connection to use — not a separate auth store.**

The browser (localhost:3000) connects to whichever Redis host/port you enter in the form. It stores its own session and user credentials in *that* Redis instance. So:
- Set `requirepass` on the Redis where FalkorDB runs
- In the browser login form: enter that same Redis's host/port + the new password
- On successful login, the browser stores credentials in Redis itself (NextAuth session store backed by Redis)
- The browser's user DB and session DB are the same Redis instance — no separate auth store

**To recover from a broken state after setting requirepass:**
Simply navigate to the login page and log in again — this time with the new password in the form. The browser will successfully connect and the session will recover. No restart needed.

## User Management
Users are managed entirely through the browser UI: Settings > Users. The browser stores user accounts in Redis. No separate auth store.

## Connection String Format
```
redis://username:password@host:port
```
Example: `redis://Default:FalkorDB2026!@localhost:6379`
