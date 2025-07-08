from fastmcp import FastMCP

mcp = FastMCP("nlp-tools")

# Import tool modules so they register with the shared mcp instance
from tools import extract_entities  # noqa: F401
from tools import generate_summary  # noqa: F401
from tools import extract_mood     # noqa: F401
from tools import generate_tags    # noqa: F401

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8003, path="/mcp") 