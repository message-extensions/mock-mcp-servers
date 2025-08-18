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

#### Simple Authentication Server (`server-dummy-auth.py`)
**Purpose**: Basic authentication testing with demo tokens
- **Port**: 3001
- **Authentication**: Simple token-based (`demo-token`)

**Features**:
- Demonstration-level authentication
- Basic weather data tools
- Simple scope validation

**Tools**:
- `get_weather(city: str)` - Get weather data for specified city

#### Multi-Authentication Server (`server-multi-auth.py`)
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

## Authentication Methods Supported

### OAuth 2.0 (Opaque Tokens)
- Token introspection endpoint validation
- Client credentials and authorization code flows
- Configurable token endpoint

### SSO JWT Tokens (Azure AD)
- Microsoft Azure AD integration
- JWT signature validation
- Automatic scope mapping from Microsoft Graph scopes
- Support for `User.Read` and `User.Write` permissions

### API Key Authentication
- Simple API key validation
- Configurable via environment variables
- Suitable for server-to-server communication

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

### Environment Configuration

#### Auth Servers
Create a `.env` file in `auth-mcp-server/` with:
```env
# SSO Configuration
SSO_ISSUER=https://sts.windows.net/72f988bf-86f1-41af-91ab-2d7cd011db47/
SSO_AUDIENCE=your-app-id
SSO_JWKS_URL=https://login.microsoftonline.com/common/discovery/v2.0/keys

# OAuth Configuration  
OAUTH_INTROSPECT_ENDPOINT=https://your-oauth-server/introspect
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret

# API Key Configuration
API_KEYS=key1,key2,key3
```

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