from typing import Optional, Dict, Any
import json
import os
from pathlib import Path
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

# Load metadata for document search and retrieval
SCRIPT_DIR = Path(__file__).parent
METADATA_FILE = SCRIPT_DIR / "metadata.json"
DOCS_DIR = SCRIPT_DIR / "docs"

def load_metadata():
    """Load document metadata from metadata.json file."""
    try:
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('documents', [])
    except Exception as e:
        print(f"Error loading metadata: {e}")
        return []

def load_document_content(filename: str) -> str:
    """Load the full text content of a document from the docs/ folder."""
    try:
        file_path = DOCS_DIR / filename
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error loading document {filename}: {e}")
        return ""

@mcp.tool()
async def search(query: str) -> str:
    """
    Search enterprise security and compliance documentation from companies. Returns documents covering data protection platforms, security audit systems, ISO frameworks, data retention policies, incident response procedures, and vendor risk assessment tools.
    
    Arguments:
        query: A single query string to search for.
    
    Returns:
        A JSON-encoded string containing search results with id, title, and url fields.
    """
    print(f"Searching for: {query}")
    
    # Load metadata
    documents = load_metadata()
    
    # Simple keyword-based search across multiple fields
    query_words = query.lower().split()
    results = []
    
    for doc in documents:
        # Search in title, summary, tags, category, and key topics
        searchable_text = " ".join([
            doc.get("title", ""),
            doc.get("summary", ""),
            doc.get("category", ""),
            " ".join(doc.get("tags", [])),
            " ".join(doc.get("key_topics", []))
        ]).lower()
        
        # Also load and search document content for more thorough results
        if doc.get("filename"):
            content = load_document_content(doc["filename"])
            searchable_text += " " + content.lower()
        
        # Check if all query words appear in searchable text
        if all(word in searchable_text for word in query_words):
            results.append({
                "id": doc.get("id"),
                "title": doc.get("title"),
                "url": doc.get("url")
            })
    
    # Return as JSON-encoded string in a results array
    response = {"results": results}
    return json.dumps(response)

@mcp.tool()
async def fetch(id: str) -> str:
    """
    Retrieve complete documentation by ID. Access detailed information about company-specific systems used by enterprises for security, compliance, and risk management operations.
    
    Arguments:
        id: A unique identifier for the search document.
    
    Returns:
        A JSON-encoded string containing the full document with id, title, text, url, and metadata fields.
    """
    print(f"Fetching document: {id}")
    
    # Load metadata
    documents = load_metadata()
    
    # Find document by ID
    document_meta = None
    for doc in documents:
        if doc.get("id") == id:
            document_meta = doc
            break
    
    if document_meta is None:
        # Return error message if document not found
        return json.dumps({
            "error": f"Document with id '{id}' not found",
            "id": id
        })
    
    # Load the full document content
    text = load_document_content(document_meta.get("filename", ""))
    
    # Construct response with document metadata and content
    response = {
        "id": document_meta.get("id"),
        "title": document_meta.get("title"),
        "text": text,
        "url": document_meta.get("url"),
        "metadata": {
            "category": document_meta.get("category"),
            "tags": document_meta.get("tags", []),
            "summary": document_meta.get("summary")
        }
    }
    
    # Return the full document as JSON-encoded string
    return json.dumps(response)

if __name__ == "__main__":
    print("Starting Enhanced Weather Service with Multi-Authentication Support...")
    print("Supported authentication methods:")
    print("  - SSO JWT tokens (Azure AD)")
    print("  - OAuth/JWT tokens (Adobe IMS)")
    print(f"Server running on http://0.0.0.0:3001/mcp")
    mcp.run(transport="streamable-http")