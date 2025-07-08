from server import mcp

@mcp.tool()
def format_text(text: str, line_length: int = 80) -> str:
    """Wrap text to the specified line length (for PDF layout)."""
    import textwrap
    return "\n".join(textwrap.wrap(text, width=line_length)) 