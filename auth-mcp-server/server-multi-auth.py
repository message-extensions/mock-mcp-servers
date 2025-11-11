from typing import Optional, Dict, Any
from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp.server.auth import TokenVerifier, AccessToken

# Custom OR-composite verifier that succeeds if any child verifier succeeds
class OrAuthVerifier(TokenVerifier):
    """Composite verifier that accepts a token if any child accepts it."""

    def __init__(self, *verifiers: TokenVerifier, required_scopes: list[str] | None = None):
        print("Initializing OrAuthVerifier with multiple verifiers...")
        super().__init__(required_scopes=required_scopes)
        self.verifiers = verifiers

    async def verify_token(self, token: str) -> Optional[AccessToken]:
        for v in self.verifiers:
            try:
                print(f"Verifying token with {v}...")
                result = await v.verify_token(token)
            except Exception:
                result = None
            if result is not None:
                print(f"Token verified successfully by {v}. Result: {result}")
                # If this composite has required scopes, enforce them here
                if self.required_scopes:
                    token_scopes = set(result.scopes)
                    required = set(self.required_scopes)
                    if not required.issubset(token_scopes):
                        continue
                return result
        return None

# Add a simple API Key verifier that checks the token equals a configured API key
class ApiKeyVerifier(TokenVerifier):
    """Simple API Key verifier initialized with a single API key string.

    This verifier will accept a bearer token if and only if the token string
    exactly matches the configured API key and will return a minimal
    AccessToken describing the API key client.
    """

    def __init__(self, api_key: str):
        # No special resource server URL or global required_scopes are used
        super().__init__()
        self.api_key = api_key
        # Provide some default metadata for the API key client
        self.client_id = "api-key-client"
        self.scopes = ["user"]

    async def verify_token(self, token: str) -> Optional[AccessToken]:
        """Return an AccessToken when the provided token matches the configured API key."""
        if token == self.api_key:
            print("API Key verified successfully")
            return AccessToken(
                token=token,
                client_id=self.client_id,
                scopes=self.scopes,
                expires_at=None,
            )
        return None

ms_sso_verifier = JWTVerifier(
    jwks_uri="https://login.microsoftonline.com/common/discovery/keys",
    issuer="https://login.microsoftonline.com/72f988bf-86f1-41af-91ab-2d7cd011db47/v2.0",
    audience="b232067f-2258-4389-84e7-9705dc203634",
    required_scopes=["User.Read"]
)

adobe_oauth_verifier = JWTVerifier(
    jwks_uri="https://ims-na1.adobelogin.com/ims/keys",
    # Adobe JWT does NOT contain any issuer or audience, so we verify only scopes
    # required_scopes=["AdobeID", "openid", "email"],
    # Due to a bug in the JWTVerifier code, the scopes string is NOT split at commas - so bypassing scopes check for now. Will update once the issue is fixed in FastMCP package.
)

entra_oauth_verifier = JWTVerifier(
    jwks_uri="https://login.microsoftonline.com/common/discovery/keys",
    issuer="https://login.microsoftonline.com/72f988bf-86f1-41af-91ab-2d7cd011db47/v2.0",
    audience="3a4f4d9b-3ae6-4bbe-b665-409dccf95599", 
    required_scopes=["MCPTools.Invoke"]
)

api_key_verifier = ApiKeyVerifier("mock_mcp_api_key")

verifier = OrAuthVerifier(ms_sso_verifier, adobe_oauth_verifier, entra_oauth_verifier, api_key_verifier)

mcp = FastMCP(name="Protected API", auth=verifier, host="0.0.0.0", port=3001, stateless_http=True)
# mcp = FastMCP(name="Protected API", host="0.0.0.0", port=3001)

@mcp.tool()
async def get_weather(city: str) -> dict[str, str]:
    """Get weather data for a city."""
    print(f"Fetching weather for {city}...")
    return {
        "city": city,
        "temperature": "22",
        "condition": "Partly cloudy",
        "humidity": "65%",
        "auth_method": "Multi-auth supported"
    }

@mcp.tool()
async def get_forecast(city: str, days: int) -> dict[str, Any]:
    """Get weather forecast for a city"""
    print(f"Fetching weather forecast for {city} for {days} days...")
    return {
        "city": city,
        "days": days,
        "forecast": [
            {"day": i+1, "temperature": f"{20+i}", "condition": "Sunny"}
            for i in range(days)
        ]
    }

# Mock data store for search and fetch functionality
MOCK_DOCUMENTS = {
    "doc1": {
        "id": "doc1",
        "title": "Introduction to MCP Servers",
        "text": "Model Context Protocol (MCP) servers provide a standardized way to expose tools and resources to AI applications. They enable secure authentication and authorization for AI agents.",
        "url": "https://example.com/docs/mcp-intro",
        "metadata": {"category": "documentation", "tags": ["mcp", "servers", "intro"]}
    },
    "doc2": {
        "id": "doc2",
        "title": "Authentication Best Practices",
        "text": "When implementing authentication in MCP servers, consider using JWT tokens, OAuth flows, or API keys. Multi-authentication support allows flexibility for different client types.",
        "url": "https://example.com/docs/auth-practices",
        "metadata": {"category": "security", "tags": ["authentication", "security", "oauth"]}
    },
    "doc3": {
        "id": "doc3",
        "title": "Weather API Integration Guide",
        "text": "This guide covers how to integrate weather APIs into your MCP server. Learn about handling city queries, forecast data, and response formatting.",
        "url": "https://example.com/docs/weather-api",
        "metadata": {"category": "tutorial", "tags": ["weather", "api", "integration"]}
    },
    "doc4": {
        "id": "doc4",
        "title": "FastMCP Framework Overview",
        "text": "FastMCP is a Python framework for building MCP servers quickly. It provides decorators for tools, built-in authentication, and HTTP transport support.",
        "url": "https://example.com/docs/fastmcp",
        "metadata": {"category": "framework", "tags": ["fastmcp", "python", "framework"]}
    },
    "doc5": {
        "id": "doc5",
        "title": "Advanced Token Verification",
        "text": "Composite token verifiers allow you to accept multiple authentication methods. The OrAuthVerifier pattern enables SSO, OAuth, and API key authentication simultaneously.",
        "url": "https://example.com/docs/token-verification",
        "metadata": {"category": "security", "tags": ["tokens", "verification", "composite"]}
    }
}

@mcp.tool()
async def search(query: str) -> str:
    """
    Search for relevant documents based on a query string.
    
    Arguments:
        query: A single query string to search for.
    
    Returns:
        A JSON-encoded string containing search results with id, title, and url fields.
    """
    import json
    
    print(f"Searching for: {query}")
    
    # Simple keyword-based search across titles and text
    query_lower = query.lower()
    results = []
    
    for doc in MOCK_DOCUMENTS.values():
        # Check if query terms appear in title or text
        if query_lower in doc["title"].lower() or query_lower in doc["text"].lower():
            results.append({
                "id": doc["id"],
                "title": doc["title"],
                "url": doc["url"]
            })
    
    # Return as JSON-encoded string in a results array
    response = {"results": results}
    return json.dumps(response)

@mcp.tool()
async def fetch(id: str) -> str:
    """
    Fetch the full contents of a document by its unique identifier.
    
    Arguments:
        id: A unique identifier for the search document.
    
    Returns:
        A JSON-encoded string containing the full document with id, title, text, url, and metadata fields.
    """
    import json
    
    print(f"Fetching document: {id}")
    
    # Retrieve document by ID
    document = MOCK_DOCUMENTS.get(id)
    
    if document is None:
        # Return error message if document not found
        return json.dumps({
            "error": f"Document with id '{id}' not found",
            "id": id
        })
    
    # Return the full document as JSON-encoded string
    return json.dumps(document)

if __name__ == "__main__":
    print("Starting Enhanced Weather Service with Multi-Authentication Support...")
    print("Supported authentication methods:")
    print("  - SSO JWT tokens (Azure AD)")
    print("  - OAuth/JWT tokens (Adobe IMS)")
    print(f"Server running on http://0.0.0.0:3001/mcp")
    mcp.run(transport="streamable-http")