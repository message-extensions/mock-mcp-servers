from typing import Optional, Dict, Any
from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp.server.auth import TokenVerifier, AccessToken

# Custom OR-composite verifier that succeeds if any child verifier succeeds
class OrAuthVerifier(TokenVerifier):
    """Composite verifier that accepts a token if any child accepts it."""

    def __init__(self, *verifiers: TokenVerifier, required_scopes: list[str] | None = None, resource_server_url: str | None = None):
        print("Initializing OrAuthVerifier with multiple verifiers...")
        super().__init__(required_scopes=required_scopes, resource_server_url=resource_server_url)
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

# Configure JWT verification against your identity providers (Microsoft SSO + Adobe OAuth)
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

verifier = OrAuthVerifier(ms_sso_verifier, adobe_oauth_verifier)


mcp = FastMCP(name="Protected API", auth=verifier, host="0.0.0.0", port=3001)
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


if __name__ == "__main__":
    print("Starting Enhanced Weather Service with Multi-Authentication Support...")
    print("Supported authentication methods:")
    print("  - SSO JWT tokens (Azure AD)")
    print("  - OAuth/JWT tokens (Adobe IMS)")
    print(f"Server running on http://0.0.0.0:3001/mcp")
    mcp.run(transport="streamable-http")