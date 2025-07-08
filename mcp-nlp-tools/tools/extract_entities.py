from server import mcp
from transformers import pipeline
from typing import Any
import dateparser

# Initialise a lightweight NER pipeline once (distilbert-base-uncased-fine-tuned-conll03-english)
_ner = pipeline("ner", grouped_entities=True)

@mcp.tool()
def extract_entities(text: str) -> dict:
    """Extract entities, dates (ISO strings), and location mentions using a transformers NER model."""

    ner_results: list[dict[str, Any]] = _ner(text)  # type: ignore[param-type]
    entities = [{"text": r.get("word", ""), "label": r.get("entity_group", "")} for r in ner_results]

    locations = [e["text"] for e in entities if e["label"] in {"LOC", "GPE"}]

    # simple date extraction using dateparser on each token span
    dates = []
    for ent in entities:
        if ent["label"] == "DATE":
            dt = dateparser.parse(ent["text"])
            if dt:
                iso = dt.date().isoformat()
                if iso not in dates:
                    dates.append(iso)

    return {"entities": entities, "dates": dates, "locations": locations} 