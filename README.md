# Mock MCP Servers

This repository contains test and mock Model Context Protocol (MCP) servers developed by the **3PCxP team** for evaluation and testing of remote MCP functionality in **Declarative Agents (DAs)**.

## Overview

The Model Context Protocol (MCP) enables seamless communication between AI assistants and external data sources, tools, and services. This repository provides various mock MCP servers that simulate different scenarios and authentication methods for comprehensive testing of MCP integrations.

## Repository Structure

```
mock-mcp-servers/
├── auth-mcp-server/          # Authentication-focused MCP servers
│   ├── server-dummy-auth.py  # Simple demo authentication server
│   ├── server-multi-auth.py  # Multi-method authentication server
│   ├── server-sso-oauth-jwt-verifier.py  # JWT composite (Microsoft SSO OR Adobe IMS)
│   ├── requirements.txt      # Python dependencies
│   ├── .env                  # Authentication configuration
│   └── Dockerfile            # Container configuration
├── rai-mcp-server/           # Responsible AI content review server
│   ├── server.py             # RAI content validation server
│   ├── requirements.txt      # Python dependencies
│   ├── Dockerfile            # Container configuration
│   └── Responsible_AI_Content_Review.csv  # Sample content data
└── DEPLOYMENT.md             # Generic deployment guide
```

## Available MCP Servers

### 1. RAI (Responsible AI) MCP Server

**Purpose**: Content validation and responsible AI testing
- **Port**: 8000
- **Image**: `tezanmcpserverregistry.azurecr.io/mcp-server:latest`
- **Deployed URL**: https://mcp-server-app.icycliff-ccab3350.eastus.azurecontainerapps.io/mcp

**Features**:
- News content search functionality
- CSV-based content validation
- Responsible AI content review capabilities
- Inspector-compatible interface

**Tools**:
- `search(query: str)` - Search for news content and validate against RAI guidelines

### 2. Authentication MCP Servers

#### [Not Used] Simple Authentication Server (`server-dummy-auth.py`)
**Purpose**: Basic authentication testing with demo tokens
- **Port**: 3001
- **Authentication**: Simple token-based (`demo-token`)

**Features**:
- Demonstration-level authentication
- Basic weather data tools
- Simple scope validation

**Tools**:
- `get_weather(city: str)` - Get weather data for specified city

#### [Not Used] Multi-Authentication Server (`server-multi-auth.py`)
**Purpose**: Advanced authentication testing with multiple auth methods
- **Port**: 3001
- **Image**: `tezanmcpserverregistry.azurecr.io/mcp-auth-server:latest`
- **Deployed URL**: https://mcp-auth-server-app.icycliff-ccab3350.eastus.azurecontainerapps.io/mcp

**Features**:
- **OAuth 2.0** support with opaque tokens
- **SSO JWT tokens** (Azure AD integration)
- **API Key** authentication
- Scope-based authorization (`weather:read`, `weather:write`)
- RFC 9728 Protected Resource Metadata compliance

**Tools**:
- `get_weather(city: str)` - Get current weather (public access)
- `get_forecast(city: str, days: int)` - Get weather forecast (requires `weather:read` scope)
- `update_weather_station(station_id: str, data: dict)` - Update weather data (requires `weather:write` scope)

#### [Deployed] SSO/OAuth JWT Composite Server (`server-sso-oauth-jwt-verifier.py`)
Purpose: Validate Bearer tokens issued by either Microsoft Entra ID (Azure AD) or Adobe IMS using JWKS. The request is authorized if either provider validates the JWT.

- Port: 3001
- Auth: OR-composite over two JWT verifiers
- Providers configured by default:
	- Microsoft SSO
		- JWKS: https://login.microsoftonline.com/common/discovery/keys
		- Issuer: https://sts.windows.net/72f988bf-86f1-41af-91ab-2d7cd011db47/
		- Audience: api://auth-e6c1573d-3ea0-4392-b2c7-0cb5209f16f2
	- Adobe IMS
		- JWKS: https://ims-na1.adobelogin.com/ims/keys
		- Issuer: https://ims-na1.adobelogin.com
		- Audience: not enforced by default (add if your tokens require it)

Features:
- Validates JWT signature and standard claims via each provider’s JWKS/issuer
- Accepts the token if any configured verifier returns a valid AccessToken
- Reuses FastMCP’s built-in JWTVerifier; no API keys or opaque tokens here

Tools:
- `get_weather(city: str)` - Get current weather
- `get_forecast(city: str, days: int)` - Get weather forecast

Run locally:
1. Install deps: `pip install -r auth-mcp-server/requirements.txt`
2. Start: `python auth-mcp-server/server-sso-oauth-jwt-verifier.py`
3. Call with Authorization header: `Authorization: Bearer <your_jwt>` from either Microsoft or Adobe

Notes:
- Defaults are hardcoded in the script; update the file to change issuer/audience.
- Keep FastMCP import from `fastmcp` (as implemented).

## Deployment

All servers are deployed to **Azure Container Apps** using **Azure Container Registry**. For detailed deployment instructions, see [`DEPLOYMENT.md`](DEPLOYMENT.md).

### Current Deployments

| Server | Container App | Port | URL |
|--------|---------------|------|-----|
| RAI Server | `mcp-server-app` | 8000 | https://mcp-server-app.icycliff-ccab3350.eastus.azurecontainerapps.io/mcp |
| Auth Server | `mcp-auth-server-app` | 3001 | https://mcp-auth-server-app.icycliff-ccab3350.eastus.azurecontainerapps.io/mcp |

## Development and Testing

### Prerequisites
- Python 3.11+
- Docker Desktop
- Azure CLI (for deployment)

### Local Development
1. Navigate to the desired server directory
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables (`.env` files)
4. Run the server: `python server.py`

## Use Cases

### For 3PCxP Team Evaluation
- **Authentication Testing**: Validate different auth flows in Declarative Agents
- **Content Moderation**: Test RAI compliance in agent interactions
- **Remote MCP Integration**: Verify MCP protocol implementation
- **Scope Authorization**: Test fine-grained permission systems
- **Multi-tenant Scenarios**: Validate client isolation and security

### Testing Scenarios
1. **Unauthenticated Access**: Test public endpoints
2. **Token Validation**: Test various token formats and validation
3. **Scope Enforcement**: Test permission-based access control
4. **Error Handling**: Test authentication failures and edge cases
5. **Content Filtering**: Test RAI content validation workflows

## Contributing

When adding new MCP servers:
1. Create a new directory following the naming convention: `{purpose}-mcp-server/`
2. Include `requirements.txt`, `Dockerfile`, and server implementation
3. Update this README with server details
4. Add deployment instructions to `DEPLOYMENT.md`
5. Test locally before deploying to Azure

## Support and Contact

For deployment updates or access to the Azure resources, contact **Tezan** (`tezansahu`).

For technical questions about the MCP implementations or testing scenarios, reach out to the **3PCxP team**.

## Security Considerations

- All servers implement proper authentication mechanisms
- Sensitive configuration is managed through environment variables
- Azure Container Apps provide secure ingress and scaling
- Token validation follows industry standards (RFC 6749, RFC 7519)
- Content validation ensures responsible AI practices

## License

This repository is for internal testing and evaluation purposes by the 3PCxP team.