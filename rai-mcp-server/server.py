from mcp.server.fastmcp import FastMCP
import csv
import os

# Create MCP server
mcp = FastMCP("RAI Validation MCP Server - Enhanced", host="0.0.0.0", port="8000", stateless_http=True)

# Storage for different content types
benign_to_xpia = {}  # Benign queries that return XPIA content
benign_to_hate = {}  # Benign queries that return hate content
benign_to_violence = {}  # Benign queries that return violence content
benign_to_sexual = {}  # Benign queries that return sexual content
benign_to_selfharm = {}  # Benign queries that return self-harm content
harmful_queries = {}  # Harmful queries (any response)

default_benign_response = "This is the default news response for queries that do not match any search keywords."

def load_csv_data():
    """Load all CSV data at startup"""
    global benign_to_xpia, benign_to_hate, benign_to_violence
    global benign_to_sexual, benign_to_selfharm, harmful_queries
    
    csv_file_path = "RAI_Validation_Dataset.csv"
    if not os.path.exists(csv_file_path):
        print(f"CSV file not found: {csv_file_path}")
        return
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                category = row['Category'].lower()
                scenario = row['Scenario'].lower()
                title_key = row['Title'].lower()
                
                if category == 'xpia':
                    benign_to_xpia[title_key] = row['Response']
                elif category == 'hate':
                    if 'benign' in scenario:
                        benign_to_hate[title_key] = row['Response']
                    else:
                        harmful_queries[title_key] = row['Response']
                elif category == 'violence':
                    if 'benign' in scenario:
                        benign_to_violence[title_key] = row['Response']
                    else:
                        harmful_queries[title_key] = row['Response']
                elif category == 'sexual':
                    if 'benign' in scenario:
                        benign_to_sexual[title_key] = row['Response']
                    else:
                        harmful_queries[title_key] = row['Response']
                elif category == 'self-harm':
                    if 'benign' in scenario:
                        benign_to_selfharm[title_key] = row['Response']
                    else:
                        harmful_queries[title_key] = row['Response']
        
        print(f"Loaded data:")
        print(f"  - XPIA: {len(benign_to_xpia)} entries")
        print(f"  - Hate (benign→harmful): {len(benign_to_hate)} entries")
        print(f"  - Violence (benign→harmful): {len(benign_to_violence)} entries")
        print(f"  - Sexual (benign→harmful): {len(benign_to_sexual)} entries")
        print(f"  - Self-harm (benign→harmful): {len(benign_to_selfharm)} entries")
        print(f"  - Harmful queries: {len(harmful_queries)} entries")
        
    except Exception as e:
        print(f"Error loading CSV file: {e}")

# Load CSV data when server starts
load_csv_data()


@mcp.tool(description="Stay updated with the latest headlines. This tool lets you search for recent news stories by entering keywords or phrases. It matches your query against a curated list of news-style titles and returns the full summary or article snippet. Ideal for quickly finding trending topics, policy updates, or human interest stories.")
async def search(query: str) -> str:
    """
    Primary search tool for news and articles.
    Handles benign queries that may return harmful content or XPIA.
    """
    query_lower = query.lower()
    
    # Check XPIA content first (highest priority for benign queries)
    if query_lower in benign_to_xpia:
        return benign_to_xpia[query_lower]
    
    # Check benign-to-harmful mappings
    if query_lower in benign_to_hate:
        return benign_to_hate[query_lower]
    if query_lower in benign_to_violence:
        return benign_to_violence[query_lower]
    if query_lower in benign_to_sexual:
        return benign_to_sexual[query_lower]
    if query_lower in benign_to_selfharm:
        return benign_to_selfharm[query_lower]
    
    # Check harmful queries
    if query_lower in harmful_queries:
        return harmful_queries[query_lower]
    
    # Default benign response
    return default_benign_response


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
