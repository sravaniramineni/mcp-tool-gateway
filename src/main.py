from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import time

app = FastAPI(title="MCP Tool Gateway")

TOOLS = {
    "lookup_customer": {"description": "Look up customer record", "sensitive": False},
    "create_ticket": {"description": "Create support ticket", "sensitive": False},
    "issue_refund": {"description": "Issue a refund", "sensitive": True},
}

audit_log = []

class ToolCall(BaseModel):
    tool: str
    arguments: dict = {}
    approval_token: str | None = None

@app.get("/tools/list")
def list_tools():
    return {"tools": TOOLS}

@app.post("/tools/call")
def call_tool(req: ToolCall, x_role: str = Header(default="agent")):
    if req.tool not in TOOLS:
        raise HTTPException(status_code=404, detail="Unknown tool")
    if TOOLS[req.tool]["sensitive"] and not req.approval_token:
        raise HTTPException(status_code=403, detail="Approval required for sensitive tool")
    entry = {"tool": req.tool, "role": x_role, "ts": time.time(), "arguments": req.arguments}
    audit_log.append(entry)
    return {"status": "ok", "result": f"Executed {req.tool}", "audit_id": len(audit_log)}

@app.get("/audit")
def audit():
    return {"events": audit_log}
