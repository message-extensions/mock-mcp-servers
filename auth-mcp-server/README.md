# Auth MCP Server (Composite JWT: Microsoft SSO OR Adobe IMS)

This folder contains the final mock MCP server we use for authentication testing and evaluations: `server-multi-auth.py`.

It exposes simple weather tools but, importantly, demonstrates a TokenVerifier-only design: the MCP server validates Bearer tokens by attempting verification against multiple JWT issuers and accepts the token if any one succeeds.

## What this server does
- Implements a composite JWT TokenVerifier that performs an OR across providers:
  - Microsoft Entra ID (Azure AD) SSO
  - Adobe IMS (JWT)
- Includes a simple API Key verifier (single-key fallback). By default this example uses the API key `mock_mcp_api_key`.
- Uses FastMCP's built-in `JWTVerifier` for each provider and composes them via `OrAuthVerifier`.
- Continues to import `FastMCP` from `fastmcp` (not `mcp.server.fastmcp`).

## Why this matters for DAs (SSO + OAuth)
- MCP protocol natively supports OAuth, but not SSO login flows.
- Microsoft SSO still works here because the SSO token is a JWT sent by Sydney to the MCP server.
- With the composite JWT verifier, we can run mock Declarative Agents (DAs) that authenticate with either:
  - Microsoft SSO (JWT from Sydney)
  - OAuth-issued JWTs (e.g., Adobe IMS)

In other words, this server serves purely as a TokenVerifier, allowing DA testing for both SSO and OAuth without implementing interactive login flows inside MCP.

## Deployment
This mock server is deployed to Azure Container Apps (same pattern as other servers in this repo). If you need the exact URL, see the root-level README's deployment table or your environment notes.

- Container app name: typically `mcp-auth-server-app`
- Port: 3001
- Endpoint path: `/mcp`

## File of interest
- `server-multi-auth.py`
  - Microsoft SSO verifier:
    - JWKS: https://login.microsoftonline.com/common/discovery/keys
    - Issuer: https://login.microsoftonline.com/72f988bf-86f1-41af-91ab-2d7cd011db47/v2.0
    - Audience: b232067f-2258-4389-84e7-9705dc203634
    - Scopes: User.Read
  - Adobe IMS verifier:
    - JWKS: https://ims-na1.adobelogin.com/ims/keys
    - Issuer/Audience: not enforced by default in this mock; adjust if needed
  - Composite:
    - `verifier = OrAuthVerifier(ms_sso_verifier, adobe_oauth_verifier, api_key_verifier)`  # includes ApiKeyVerifier (default key: `mock_mcp_api_key`)
  - FastMCP wiring:
    - Auth-enabled line (default):
      - `mcp = FastMCP(name="Protected API", auth=verifier, host="0.0.0.0", port=3001)`
    - Auth-disabled line (commented):
      - `# mcp = FastMCP(name="Protected API", host="0.0.0.0", port=3001)`

## ATK (Agent Toolkit) and VS Code MCP Client caveat
When creating a DA and clicking "Fetch tools from MCP server", the VS Code MCP Client may prompt for authorization. The recommended approach in FastMCP is to implement an OAuth Proxy in the MCP server (see docs: https://gofastmcp.com/servers/auth/oauth-proxy) for ID Providers that do not support Dynamic Client Registration (DCR). However, the latest FastMCP with this feature is not yet available on PyPI.

### Workaround steps
During DA creation, temporarily disable auth just for the tool-fetch step, then restore it:
1. In `server-multi-auth.py`:
   - Comment the auth-enabled FastMCP line (currently around line ~80):
     - `mcp = FastMCP(name="Protected API", auth=verifier, host="0.0.0.0", port=3001)`
   - Uncomment the no-auth FastMCP line just below it:
     - `# mcp = FastMCP(name="Protected API", host="0.0.0.0", port=3001)` → remove the leading `#`
2. Deploy or run locally and perform "Fetch tools from MCP server" in VS Code.
3. Once `ai-plugin.json` in the DA manifest is populated, revert the change to re-enable auth and redeploy/restart.

Additionally, in your DA's `ai-plugin.json`, under the `RemoteMCPServer` runtime, you can manually populate the `auth` field thereafter to reflect the token strategy you'll use.

## Local run
- Install: `pip install -r requirements.txt`
- Run: `python server-multi-auth.py`
- Call with header: `Authorization: Bearer <jwt-from-azure-or-adobe>` or `Authorization: Bearer mock_mcp_api_key`

## Notes
- Adobe tokens may not include issuer/audience in all flows; adjust the verifier if your tokens require stricter checks.
- Scope parsing differences across IdPs exist; validate scopes as needed.
- This mock is strictly for testing/evaluation; do not use as-is in production.
