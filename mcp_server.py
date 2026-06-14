# mcp_server.py
from mcp.server.fastmcp import FastMCP
from src.server.DB_API import DB_API
import logging

# Initialize the MCP Server
mcp = FastMCP("FindMyPatient-Data-Server")
db = DB_API()

logging.basicConfig(level=logging.INFO)

@mcp.tool()
def execute_mongo_query(query: dict) -> str:  
    """
    Executes a MongoDB aggregation pipeline on the patient database.
    
    Args:
        query: A dictionary representing a valid MongoDB query.
    """
    try:
        # Check if the LLM wrapped the query in a dictionary with a 'pipeline' key
        if "pipeline" in query:
            actual_query = query["pipeline"]
        else:
            # Sometimes it just generates the direct dictionary/list
            actual_query = [query] if isinstance(query, dict) else query
            
        result = db.CustomAggregationQuery(actual_query)
        return str(result)
    except Exception as e:
        return f"Database execution error: {str(e)}"
    
if __name__ == "__main__":
    print("Starting FindMyPatient MCP Server on stdio...")
    mcp.run()