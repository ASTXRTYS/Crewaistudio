from server import mcp
import re

POSITIVE_WORDS = {"good", "great", "excellent", "happy", "love", "awesome", "fantastic"}
NEGATIVE_WORDS = {"bad", "terrible", "sad", "angry", "hate", "awful", "horrible"}

@mcp.tool()
def extract_mood(text: str) -> float:
    """Return a simple mood score between -1 (very negative) and 1 (very positive)."""
    words = re.findall(r"[A-Za-z']+", text.lower())
    if not words:
        return 0.0
    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)
    score = (pos - neg) / (pos + neg) if (pos + neg) else 0.0
    return score 