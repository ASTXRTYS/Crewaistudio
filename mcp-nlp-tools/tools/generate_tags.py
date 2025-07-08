from server import mcp
import re
from collections import Counter

_STOPWORDS = {
    "the", "and", "a", "an", "to", "of", "in", "on", "for", "with", "at", "by", "from", "up", "about", "into", "over", "after",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "but", "if", "or", "because", "as",
}


@mcp.tool()
def generate_tags(text: str, top_k: int = 5) -> list[str]:
    """Return top_k frequent keywords (length>=4) from the text."""
    words = re.findall(r"[A-Za-z']+", text.lower())
    candidates = [w for w in words if len(w) >= 4 and w not in _STOPWORDS]
    most_common = [w for w, _ in Counter(candidates).most_common(top_k)]
    return most_common 