from server import mcp
from pypdf import PdfReader

@mcp.tool()
def read_pdf_text(file_path: str, max_pages: int | None = None) -> str:
    """Extract text from a PDF. Optionally limit to first `max_pages`."""
    reader = PdfReader(file_path)
    pages = reader.pages[:max_pages] if max_pages else reader.pages
    return "\n".join(page.extract_text() or "" for page in pages) 