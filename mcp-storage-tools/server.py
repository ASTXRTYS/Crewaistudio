from fastmcp import FastMCP

mcp = FastMCP("storage-tools")

# import modules (will register)  # noqa: F401
from tools import vector_store  # type: ignore

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8004, path="/mcp") 