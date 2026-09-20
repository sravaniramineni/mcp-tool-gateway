# MCP Tool Gateway

A secure gateway that lets AI agents call enterprise tools (lookup customer, create ticket, issue refund) — with scoped HMAC auth, per-subject rate limiting, idempotent execution, human approval for sensitive tools, and a full audit log.

## When to use this

Agents are powerful only when they can *do* things, but wiring an agent straight into your ERP or billing API is how you end up with an unauthorized refund at 3am. Use this as the front door: agents authenticate, prove they hold the right scope, and every call is logged and replayable.

## How it works

1. **Issue a token** — `POST /token?subject=<name>&scopes=<csv>` returns a signed token carrying the caller's scopes.
2. **Discover tools** — `GET /tools/list` returns the registered tools, their descriptions, and sensitivity flags.
3. **Call a tool** — `POST /tools/call` with `Authorization: Bearer <token>`. The gateway checks:
   - token validity (401 if bad)
   - rate limit: 60 calls / 60s per subject (429 if exceeded)
   - the caller's scopes cover the tool (403 if not)
   - **sensitive tools** (e.g. `issue_refund`) require an `approval_token` (403 if missing)
   - **idempotency**: repeat a call with the same `idempotency_key` and it's not executed twice
4. **Audit everything** — `GET /audit` returns the full event log.

## Project structure

```
src/main.py        FastAPI service: /token, /tools/list, /tools/call, /audit
src/auth.py        HMAC token issuance + verification (scoped)
docs/ARCHITECTURE.md   Design and threat model
docs/ADR-001.md        Why HMAC tokens instead of sessions
Dockerfile           Container image
.github/workflows/ci.yml   CI on every push
```

## Prerequisites

- Python 3.11+

## Quickstart

```bash
pip install -r requirements.txt
uvicorn src.main:app --reload
```

Get a token, list tools, and call one:

```bash
# 1. Issue a token with read + write scopes
TOKEN=$(curl -s -X POST "http://localhost:8000/token?subject=agent-1&scopes=read,write" | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")

# 2. See what tools exist
curl http://localhost:8000/tools/list

# 3. Call a non-sensitive tool
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"tool": "lookup_customer", "arguments": {"customer_id": "C-1001"}}'

# 4. A sensitive tool without approval is rejected (403)
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"tool": "issue_refund", "arguments": {"order_id": "O-99"}}'

# 5. Idempotency: same key twice = executed once
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"tool": "create_ticket", "idempotency_key": "req-123", "arguments": {"title": "VPN down"}}'

# 6. Review the audit trail
curl http://localhost:8000/audit
```

Expected results: step 4 returns `403 Approval required for sensitive tool`; the second identical `req-123` call returns `{"status": "duplicate", ...}` instead of executing again.

## Running the tests / CI

Every push runs the test suite via `.github/workflows/ci.yml`. Run it locally:

```bash
python -m pytest  # add tests/ as the suite grows
```

## Deploy with Docker

```bash
docker build -t mcp-tool-gateway .
docker run -p 8000:8000 mcp-tool-gateway
```

## Taking this to production

- Move the in-memory tool registry, rate limiter, and audit log to Redis/Postgres.
- Issue approval tokens from a real human-approval workflow (see the `power-automate-intelligent-approvals` repo).
- Add tool JSON schemas so agents get typed argument validation, and per-tool scopes instead of coarse `read/write/finance`.

## Further reading

- `docs/ARCHITECTURE.md` — design and threat model
- `docs/ADR-001.md` — why HMAC tokens instead of sessions
