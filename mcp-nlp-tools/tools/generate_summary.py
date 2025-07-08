from server import mcp
from transformers import pipeline
from typing import Any

_summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")


@mcp.tool()
def generate_summary(text: str, max_sentences: int = 3) -> str:
    """Generate an abstractive summary of roughly `max_sentences` sentences using a transformers model."""
    result: list[dict[str, Any]] = _summarizer(text, max_length=max_sentences * 30, min_length=max_sentences * 10, do_sample=False)  # type: ignore[arg-type]
    return result[0].get("summary_text", "") 