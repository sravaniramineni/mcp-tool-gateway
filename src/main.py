from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import time
from .auth import verify_token, issue_token

app = FastAPI(title="MCP Tool Gateway")

TOOLS = {
    "lookup_customer": {"description": "Look up customer record", "sensitive": False, "scope": "read"},
    "create_ticket": {"description": "Create support ticket", "sensitive": False, "scope": "write"},
    "issue_refund": {"description": "Issue a refund", "sensitive": True, "scope": "finance"},
}

audit_log: list[dict] = []
# naive in-memory rate limiter: (subject -> [timestamps])
_rate: dict[str, list[float]] = {}

class ToolCall(BaseModel):
    tool: str
    arguments: dict = {}
    approval_token: str | None = None
    idempotency_key: str | None = None

def _check_rate(subject: str, limit: int = 60, window: int = 60):
    now = time.time()
    hits = [t for t in _rate.get(subject, []) if now - t < window]
    if len(hits) >= limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    hits.append(now)
    _rate[subject] = hits

@app.post("/token")
def token(subject: str, scopes: str = "read"):
    return {"token": issue_token(subject, scopes.split(","))}

@app.get("/tools/list")
def list_tools():
    return {"tools": TOOLS}

@app.post("/tools/call")
def call_tool(req: ToolCall, authorization: str = Header(default="")):
    claims = verify_token(authorization.replace("Bearer ", ""))
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid token")
    _check_rate(claims["subject"])
    if req.tool not in TOOLS:
        raise HTTPException(status_code=404, detail="Unknown tool")
    meta = TOOLS[req.tool]
    if meta["scope"] not in claims["scopes"]:
        raise HTTPException(status_code=403, detail="Missing scope")
    if meta["sensitive"] and not req.approval_token:
        raise HTTPException(status_code=403, detail="Approval required for sensitive tool")
    if req.idempotency_key and any(e.get("idempotency_key") == req.idempotency_key for e in audit_log):
        return {"status": "duplicate", "result": "Already executed; not repeated."}
    entry = {"tool": req.tool, "subject": claims["subject"], "ts": time.time(),
             "arguments": req.arguments, "idempotency_key": req.idempotency_key}
    audit_log.append(entry)
    return {"status": "ok", "result": f"Executed {req.tool}", "audit_id": len(audit_log)}

@app.get("/audit")
def audit():
    return {"events": audit_log}
