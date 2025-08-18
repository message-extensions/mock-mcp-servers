import os
import re
import jwt
import requests
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import AnyHttpUrl
from fastapi import HTTPException

from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP

class MultiAuthTokenVerifier(TokenVerifier):
    """Multi-authentication token verifier supporting OAuth, SSO, and API Keys."""

    def __init__(self):
        """Initialize the verifier with configuration from environment variables."""
        # OAuth Configuration (for opaque tokens)
        self.oauth_access_token = {
                "client_id": "oauth-client-1",
                "scopes": ["weather:read", "user"],
                "subject": "oauth-user-1"
            }
        
        # SSO Configuration (expected issuer and audience for JWT validation)
        self.sso_issuer = os.getenv("SSO_ISSUER", "https://sts.windows.net/72f988bf-86f1-41af-91ab-2d7cd011db47/")
        self.sso_audience = os.getenv("SSO_AUDIENCE", "api://auth-e6c1573d-3ea0-4392-b2c7-0cb5209f16f2")
        
        # API Key Configuration
        self.valid_api_keys = {
            os.getenv("API_KEY_1", "weather-api-key-123"): {
                "client_id": "weather-client-1",
                "scopes": ["weather:read", "user"],
                "subject": "api-client-1"
            },
            os.getenv("API_KEY_2", "admin-api-key-456"): {
                "client_id": "admin-client",
                "scopes": ["weather:read", "weather:write", "admin", "user"],
                "subject": "api-admin"
            }
        }

    async def verify_token(self, token: str) -> AccessToken | None:
        """
        Verify tokens from multiple authentication sources.
        
        Args:
            token: The token to verify (can be JWT, OAuth opaque token, or API key)
            
        Returns:
            AccessToken if valid, None if invalid
        """
        # Try SSO JWT token verification first (if it looks like a JWT)
        if self._is_jwt_token(token):
            access_token = await self._verify_sso_jwt_token(token)
            if access_token:
                return access_token

        # Try OAuth opaque token verification
        access_token = await self._verify_oauth_token(token)
        if access_token:
            return access_token

        # Try API Key verification
        access_token = await self._verify_api_key(token)
        if access_token:
            return access_token

        # Token not recognized by any method
        return None

    def _is_jwt_token(self, token: str) -> bool:
        """Check if token appears to be a JWT (has 3 parts separated by dots)."""
        return len(token.split('.')) == 3

    async def _verify_oauth_token(self, token: str) -> AccessToken | None:
        """Verify OAuth opaque tokens - just presence"""
        if token != None and token != "" and not (len(token) < 30 or len(token) > 500):  # Arbitrary safe bounds
            token_info = self.oauth_access_token
            print("OAuth Token Verified Successfully")
            return AccessToken(
                token=token,
                client_id=token_info["client_id"],
                scopes=token_info["scopes"],
                expires_at=None  # OAuth tokens managed externally
            )
        return None

    async def _verify_sso_jwt_token(self, token: str) -> AccessToken | None:
        """Verify SSO JWT tokens with specific validation requirements."""
        try:
            # Decode JWT without signature verification for demo
            # In production, you should verify the signature
            decoded = jwt.decode(
                token, 
                options={"verify_signature": False},  # DO NOT USE IN PRODUCTION
                algorithms=["RS256", "HS256"]
            )
            
            # Validate SSO-specific requirements
            if not self._validate_sso_jwt_claims(decoded):
                return None

            # Extract token information
            subject = decoded.get("sub")
            oid = decoded.get("oid")  # Object ID from Azure AD
            client_id = decoded.get("appid", decoded.get("azp", "sso-client"))
            
            # Convert Microsoft scopes to weather scopes
            scp_scopes = decoded.get("scp", "").split() if "scp" in decoded else []
            scopes = self._convert_microsoft_scopes_to_weather_scopes(scp_scopes)
            
            expires_at = decoded.get("exp")
            
            print("SSO JWT Token Verified Successfully")
            print(f"User: {decoded.get('name', 'Unknown')}")
            print(f"OID: {oid}")
            print(f"Converted scopes: {scopes}")

            return AccessToken(
                token=token,
                client_id=client_id,
                scopes=scopes,
                expires_at=expires_at
            )

        except jwt.InvalidTokenError as e:
            print(f"JWT Token validation failed: {e}")
            return None

    def _validate_sso_jwt_claims(self, decoded: Dict[str, Any]) -> bool:
        """Validate JWT claims for SSO tokens with specific requirements."""
        # Check issuer (iss)
        if decoded.get("iss") != self.sso_issuer:
            print(f"Invalid issuer: {decoded.get('iss')} != {self.sso_issuer}")
            return False
            
        # Check audience (aud)
        aud = decoded.get("aud")
        if isinstance(aud, list):
            if self.sso_audience not in aud:
                print(f"Invalid audience: {self.sso_audience} not in {aud}")
                return False
        elif aud != self.sso_audience:
            print(f"Invalid audience: {aud} != {self.sso_audience}")
            return False
            
        # Check presence of oid (Object ID)
        if not decoded.get("oid"):
            print("Missing required claim: oid")
            return False
            
        # Check expiration
        exp = decoded.get("exp")
        print(exp)
        print(datetime.fromtimestamp(exp, tz=timezone.utc))
        print(datetime.now(tz=timezone.utc))
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(tz=timezone.utc):
            print("Token has expired")
            return False
            
        return True

    def _convert_microsoft_scopes_to_weather_scopes(self, scp_scopes: list[str]) -> list[str]:
        """Convert Microsoft Graph scopes to weather API scopes."""
        weather_scopes = ["user"]  # Always include user scope
        
        for scope in scp_scopes:
            if scope == "User.Read":
                weather_scopes.append("weather:read")
            elif scope == "User.Write":
                weather_scopes.append("weather:write")
        
        return list(set(weather_scopes))  # Remove duplicates

    async def _verify_api_key(self, token: str) -> AccessToken | None:
        """Verify API Key authentication."""
        if token in self.valid_api_keys:
            key_info = self.valid_api_keys[token]
            print("API Key Verified Successfully")
            return AccessToken(
                token=token,
                client_id=key_info["client_id"],
                scopes=key_info["scopes"],
                expires_at=None  # API keys don't expire in this demo
            )
        return None

# Create a global instance to access current user context
token_verifier = MultiAuthTokenVerifier()

class AuthContext:
    """Thread-local storage for current user context."""
    _current_user: Optional[AccessToken] = None
    
    @classmethod
    def set_current_user(cls, user: AccessToken):
        cls._current_user = user
    
    @classmethod
    def get_current_user(cls) -> Optional[AccessToken]:
        return cls._current_user
    
    @classmethod
    def require_scopes(cls, *required_scopes: str) -> AccessToken:
        """Check if current user has required scopes."""
        current_user = cls.get_current_user()
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        user_scopes = set(current_user.scopes)
        missing_scopes = set(required_scopes) - user_scopes
        
        if missing_scopes:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Missing scopes: {', '.join(missing_scopes)}"
            )
        
        return current_user

# Custom TokenVerifier that sets user context
class ContextAwareTokenVerifier(MultiAuthTokenVerifier):
    """Token verifier that sets the current user context."""
    
    async def verify_token(self, token: str) -> AccessToken | None:
        access_token = await super().verify_token(token)
        if access_token:
            AuthContext.set_current_user(access_token)
        return access_token

# Create FastMCP instance as a Resource Server with enhanced authentication
mcp = FastMCP(
    "Enhanced Weather Service with Multi-Auth",
    # Enhanced token verifier supporting multiple auth methods
    token_verifier=ContextAwareTokenVerifier(),
    # Auth settings for RFC 9728 Protected Resource Metadata
    auth=AuthSettings(
        issuer_url=AnyHttpUrl(os.getenv("SSO_ISSUER", "https://sts.windows.net/72f988bf-86f1-41af-91ab-2d7cd011db47/")),
        resource_server_url=AnyHttpUrl(f"http://0.0.0.0:3001/mcp"),
        required_scopes=["user"],
        # Additional metadata for clients
        token_endpoint=AnyHttpUrl(f"{os.getenv('SSO_ISSUER', 'https://sts.windows.net/72f988bf-86f1-41af-91ab-2d7cd011db47/')}/oauth2/v2.0/token"),
        authorization_endpoint=AnyHttpUrl(f"{os.getenv('SSO_ISSUER', 'https://sts.windows.net/72f988bf-86f1-41af-91ab-2d7cd011db47/')}/oauth2/v2.0/authorize"),
    ),
    host="0.0.0.0",
    port=3001
)

@mcp.tool()
async def get_weather(city: str = "London") -> dict[str, str]:
    """Get weather data for a city."""
    return {
        "city": city,
        "temperature": "22",
        "condition": "Partly cloudy",
        "humidity": "65%",
        "auth_method": "Multi-auth supported"
    }

@mcp.tool()
async def get_forecast(city: str = "London", days: int = 5) -> dict[str, Any]:
    """Get weather forecast for a city (requires weather:read scope)."""
    # Check if user has required scope
    current_user = AuthContext.require_scopes("weather:read")
    
    return {
        "city": city,
        "days": days,
        "forecast": [
            {"day": i+1, "temperature": f"{20+i}", "condition": "Sunny"}
            for i in range(days)
        ],
        "authorized_user": current_user.client_id
    }

@mcp.tool()
async def update_weather_station(station_id: str, data: dict = None) -> dict[str, str]:
    """
    Update weather station data (requires weather:write scope).
    This is an admin function that requires elevated permissions.
    """
    # Check if user has required scope
    current_user = AuthContext.require_scopes("weather:write")
    
    if data is None:
        data = {
            "temperature": 25.5,
            "humidity": 68,
            "pressure": 1013.2,
            "wind_speed": 12.3,
            "wind_direction": "NW",
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    return {
        "station_id": station_id,
        "status": "updated",
        "timestamp": datetime.now().isoformat(),
        "message": "Weather station data updated successfully",
        "updated_by": current_user.client_id,
        "client_id": current_user.client_id
    }

if __name__ == "__main__":
    print("Starting Enhanced Weather Service with Multi-Authentication Support...")
    print("Supported authentication methods:")
    print("  - OAuth 2.0 (opaque tokens)")
    print("  - SSO JWT tokens (Azure AD)")
    print("  - API Keys")
    print(f"Server running on http://0.0.0.0:3001/mcp")
    mcp.run(transport="streamable-http")