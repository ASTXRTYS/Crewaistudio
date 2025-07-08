from fastmcp import FastMCP

# Create server instance
mcp = FastMCP("pdf-processing-tools")

# Import tool modules (they will register themselves via the shared `mcp`)
from tools import pdf_reader, pdf_writer, pdf_merger, text_formatter  # noqa: F401

if __name__ == "__main__":
    # Expose via streamable-http transport on /mcp (port 8002)
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8002, path="/mcp") 