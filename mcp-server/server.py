from fastmcp import FastMCP

mcp = FastMCP("local-tools")


@mcp.tool()
def echo(text: str) -> str:
    """Echo back the supplied text."""
    return text


if __name__ == "__main__":
    # Expose MCP over streamable-http on /mcp
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8001, path="/mcp") 