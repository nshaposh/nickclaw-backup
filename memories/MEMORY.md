2026-03-21 - First session > What happened: First boot. Got named "Nickclaw" by Nick
§
2026-03-21 - First session > What happened: Nick wants to learn how to build AI agents for businesses using OpenClaw
§
2026-03-21 - First session > What happened: Nick's business idea: provide AI agents for businesses based on OpenClaw
§
2026-03-21 - First session > Notes: Nickclaw's workspace set up
§
2026-03-21 - First session > Notes: IDENTITY.md and USER.md created
§
2026-03-21 - First session > Notes: Nick's core focus: document understanding, parsing (LlamaIndex), structured storage, vectorization, RAG pipelines
§
2026-04-11 - FalkorDB exploration (continued)
§ FalkorDB Browser UI: logged in successfully at http://localhost:3000
§ Browser version: v1.9.3, FalkorDB server: v4.18.00
§ Default user: username "Default", password just set to "FalkorDB2026!" (was blank/default)
§ Browser is built into the docker image (Next.js app at /var/lib/falkordb/browser)
§ User management: done via browser UI (Settings > Users) — users stored IN Redis itself
§ Browser uses NextAuth — credentials verified against Redis, not env files
§ The 500 error after setting requirepass was because the browser was trying to connect to Redis without the password
§ Fix: restart the browser container, or set the password via redis-cli then reconnect with updated credentials
§ CORS: ALLOWED_ORIGINS currently only localhost:3000 — needs updating for remote access
§ Demos available: IMDB demo, Social graph demo (in repo demos/ folder)
§
2026-04-11 - FalkorDB connection (host machine perspective):
§ Docker bridge gateway: 172.17.0.1:6379 (no auth for Python client)
§ Browser UI: localhost:3000 (no auth)
§ Password (for browser login or authenticated Redis): FalkorDB2026!
§ FalkorDB v4.18.00, Browser v1.9.3
§ Python client: pip install falkordb
§ Loaded IMDB demo: graph "imdb" — 1317 actors, 283 movies, 1839 act relationships, <1MB