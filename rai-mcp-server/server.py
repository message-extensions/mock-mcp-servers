from mcp.server.fastmcp import FastMCP
import csv
import os

# Create MCP server
mcp = FastMCP("Responsible AI (RAI) Validation MCP Server (Inspector Compatible)", host="0.0.0.0", port="8000")

default_response = "As remote work becomes a permanent fixture across industries, companies are increasingly hiring talent from diverse geographies. This shift not only expands access to skilled professionals but also brings new challenges in managing distributed teams, ensuring time zone alignment, and maintaining organizational culture."

# Load CSV data at startup
csv_data = {}
def load_csv_data():
    global csv_data
    csv_file_path = "Responsible_AI_Content_Review.csv"
    if os.path.exists(csv_file_path):
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Store with lowercase title as key for case-insensitive lookup
                    csv_data[row['Title'].lower()] = row['Text']
            print(f"Loaded {len(csv_data)} entries from CSV file")
        except Exception as e:
            print(f"Error loading CSV file: {e}")
            csv_data = {}
    else:
        print("CSV file not found, using fallback search responses")

# Load CSV data when server starts
load_csv_data()


@mcp.tool(description="Stay updated with the latest headlines. This tool lets you search for recent news stories by entering keywords or phrases. It matches your query against a curated list of news-style titles and returns the full summary or article snippet. Ideal for quickly finding trending topics, policy updates, or human interest stories.")
def search(query: str) -> str:
    global call_count
    
    # Check pre-loaded CSV data first
    query_lower = query.lower()
    if query_lower in csv_data:
        return csv_data[query_lower]
    else:
        return default_response

if __name__ == "__main__":
    mcp.run(transport="streamable-http")