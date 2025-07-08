from server import mcp
from reportlab.pdfgen import canvas

@mcp.tool()
def write_pdf(text: str, output_file: str = "output.pdf") -> str:
    """Create a simple single-page PDF containing the supplied text."""
    c = canvas.Canvas(output_file)
    for i, line in enumerate(text.split("\n"), start=750):
        c.drawString(50, i, line)
        i -= 15
    c.save()
    return output_file 