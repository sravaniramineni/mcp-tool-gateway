# MCP Tool Gateway

Secure gateway that exposes enterprise tools and APIs to AI agents via MCP-style tool calls.

## Problem
Agents need real tools, but direct API access is risky without auth, scoping, and audit trails.

## What it does
- Tool registry with schemas
- Scoped tool invocation with RBAC header check
- Audit log for every tool call
- Safe defaults: deny-by-default, human approval for sensitive tools

## Architecture
See `docs/ARCHITECTURE.md`.

## Quickstart
```bash
pip install -r requirements.txt
uvicorn src.main:app --reload
```
