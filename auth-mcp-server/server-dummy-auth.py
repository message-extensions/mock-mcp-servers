from pydantic import AnyHttpUrl

from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP


class SimpleTokenVerifier(TokenVerifier):
    """Simple token verifier for demonstration."""

    async def verify_token(self, token: str) -> AccessToken | None:
        # Simple demonstration - accept any token that equals "demo-token"
        if token == "demo-token":
            return AccessToken(
                token=token,  # The actual token value
                subject="demo-user",  # User identifier
                client_id="demo-client",  # Client identifier
                scopes=["user"],  # List of granted scopes
                expires_at=None  # Never expires for demo (can be timestamp)
            )
        return None  # Invalid token


# Create FastMCP instance as a Resource Server
mcp = FastMCP(
    "Weather Service",
    # Token verifier for authentication
    token_verifier=SimpleTokenVerifier(),
    # Auth settings for RFC 9728 Protected Resource Metadata
    auth=AuthSettings(
        issuer_url=AnyHttpUrl("https://auth.example.com"),  # Authorization Server URL
        resource_server_url=AnyHttpUrl("http://0.0.0.0:3001/mcp"),  # This server's URL
        required_scopes=["user"],
    ),
    host="0.0.0.0",
    port =3001
)


@mcp.tool()
async def get_weather(city: str = "London") -> dict[str, str]:
    """Get weather data for a city"""
    return {
        "city": city,
        "temperature": "22",
        "condition": "Partly cloudy",
        "humidity": "65%",
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")