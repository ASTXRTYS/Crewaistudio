from server import mcp
from pypdf import PdfMerger

@mcp.tool()
def merge_pdfs(input_files: list[str], output_file: str = "merged.pdf") -> str:
    """Merge multiple PDF files into a single PDF."""
    merger = PdfMerger()
    for f in input_files:
        merger.append(f)
    merger.write(output_file)
    merger.close()
    return output_file 