# Architecture

## Flow
1. Agent lists available tools.
2. Agent calls a tool with arguments.
3. Gateway checks scope/RBAC and policy.
4. Sensitive tools require approval token.
5. Every call is audit-logged.

## Key decisions
- Deny-by-default tool registry.
- PII and financial tools are approval-gated.
- Tool schemas are versioned.

## Production hardening
- Use real MCP SDK, OAuth/OIDC, per-tenant keys, and SIEM export.
