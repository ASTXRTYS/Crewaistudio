from server import mcp
import chromadb
from sentence_transformers import SentenceTransformer
from typing import Any, List

# initialise singleton components
_client = chromadb.Client()
_collection = _client.get_or_create_collection("entries")
_model = SentenceTransformer("all-MiniLM-L6-v2")

@mcp.tool()
def add_entry(text: str, metadata: dict[str, Any] | None = None) -> str:
    """Add a text entry to the vector store. Returns entry id."""
    idx = str(len(_collection.get()["ids"]))
    embedding = _model.encode(text).tolist()
    _collection.add(ids=[idx], embeddings=[embedding], documents=[text], metadatas=[metadata or {}])
    return idx

@mcp.tool()
def semantic_search(query: str, k: int = 5) -> List[dict[str, Any]]:
    """Return top-k similar entries for the given query."""
    q_emb = _model.encode(query).tolist()
    res = _collection.query(query_embeddings=[q_emb], n_results=k)
    results = []
    for i in range(len(res["ids"][0])):
        results.append({
            "id": res["ids"][0][i],
            "score": res["distances"][0][i],
            "text": res["documents"][0][i],
            "metadata": res["metadatas"][0][i],
        })
    return results

@mcp.tool()
def list_entries() -> List[str]:
    """List all entry IDs currently stored."""
    return _collection.get()["ids"] 