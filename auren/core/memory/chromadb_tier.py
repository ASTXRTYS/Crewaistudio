"""Vector store implementation for biometric protocols"""
import hashlib
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import chromadb
import numpy as np
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


class BiometricVectorStore:
    """Vector store optimized for biometric protocol data"""

    def __init__(self, persist_directory: str = "/auren/data/vectors"):
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))

        # Initialize ChromaDB
        self.client = chromadb.Client(
            Settings(chroma_db_impl="duckdb+parquet", persist_directory=persist_directory)
        )

        # Create collections for each protocol
        self.collections = {
            "journal": self._get_or_create_collection("journal_protocol"),
            "mirage": self._get_or_create_collection("mirage_protocol"),
            "visor": self._get_or_create_collection("visor_protocol"),
            "convergence": self._get_or_create_collection("convergence_insights"),
        }

    def _get_or_create_collection(self, name: str):
        """Get or create a collection"""
        try:
            return self.client.get_collection(name)
        except:
            return self.client.create_collection(name=name, metadata={"hnsw:space": "cosine"})

    def add_protocol_entry(self, protocol: str, entry: Dict, metadata: Optional[Dict] = None):
        """Add a protocol entry to the vector store"""

        if protocol not in self.collections:
            raise ValueError(f"Unknown protocol: {protocol}")

        # Generate document ID
        doc_id = hashlib.sha256(
            f"{protocol}:{entry.get('id', '')}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        # Create searchable text
        if protocol == "journal":
            text = self._format_journal_entry(entry)
        elif protocol == "mirage":
            text = self._format_mirage_entry(entry)
        elif protocol == "visor":
            text = self._format_visor_entry(entry)
        else:
            text = json.dumps(entry)

        # Generate embedding
        embedding = self.embedding_model.encode(text).tolist()

        # Prepare metadata
        meta = metadata or {}
        meta.update(
            {
                "protocol": protocol,
                "timestamp": entry.get("timestamp", datetime.now().isoformat()),
                "entry_type": entry.get("type", "unknown"),
            }
        )

        # Add to collection
        self.collections[protocol].add(
            embeddings=[embedding], documents=[text], metadatas=[meta], ids=[doc_id]
        )

    def _format_journal_entry(self, entry: Dict) -> str:
        """Format journal entry for embedding"""

        parts = []

        if entry.get("type") == "peptide_dose":
            parts.append(
                f"Peptide administration: {entry['data']['compound']} {entry['data']['dose']}{entry['data']['unit']}"
            )
        elif entry.get("type") == "weight_log":
            parts.append(f"Weight measurement: {entry['data']['weight']}{entry['data']['unit']}")
        elif entry.get("type") == "macro_log":
            parts.append(
                f"Nutrition: {entry['data']['calories']} calories, {entry['data']['protein']}g protein"
            )

        if entry.get("notes"):
            parts.append(f"Notes: {entry['notes']}")

        return " ".join(parts)

    def _format_mirage_entry(self, entry: Dict) -> str:
        """Format MIRAGE entry for embedding"""

        scores = entry.get("scores", {})
        parts = [
            f"MIRAGE biometric analysis:",
            f"Inflammation: {scores.get('inflammation', 0)}/5",
            f"Ptosis: {scores.get('ptosis', 0)}/10",
            f"Symmetry: {scores.get('symmetry', 0)}/5",
            f"Lymphatic fullness: {scores.get('lymphatic_fullness', 0)}/5",
        ]

        if entry.get("alerts"):
            parts.append(f"Alerts: {', '.join(entry['alerts'])}")

        return " ".join(parts)

    def _format_visor_entry(self, entry: Dict) -> str:
        """Format VISOR entry for embedding"""

        return f"Visual documentation: {entry.get('purpose', '')} - {entry.get('miris_tag', '')}"

    def search(
        self,
        query: str,
        protocol: Optional[str] = None,
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None,
    ) -> List[Dict]:
        """Search for relevant entries"""

        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()

        # Search in specified protocol or all
        if protocol and protocol in self.collections:
            collections_to_search = [self.collections[protocol]]
        else:
            collections_to_search = list(self.collections.values())

        all_results = []

        for collection in collections_to_search:
            # Build where clause
            where = {}
            if filter_metadata:
                where.update(filter_metadata)

            # Search
            results = collection.query(
                query_embeddings=[query_embedding], n_results=top_k, where=where if where else None
            )

            # Format results
            for i in range(len(results["ids"][0])):
                all_results.append(
                    {
                        "id": results["ids"][0][i],
                        "document": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i],
                    }
                )

        # Sort by distance and return top k
        all_results.sort(key=lambda x: x["distance"])
        return all_results[:top_k]

    def search_by_timeframe(
        self, start_date: datetime, end_date: datetime, protocol: Optional[str] = None
    ) -> List[Dict]:
        """Search entries within a timeframe"""

        # This is a simplified implementation
        # In production, you'd use metadata filtering
        where = {
            "$and": [
                {"timestamp": {"$gte": start_date.isoformat()}},
                {"timestamp": {"$lte": end_date.isoformat()}},
            ]
        }

        if protocol:
            where["protocol"] = protocol

        return self.search("", filter_metadata=where, top_k=100)

    def find_similar_entries(self, entry: Dict, protocol: str, top_k: int = 5) -> List[Dict]:
        """Find similar entries to a given entry"""

        # Format entry as text
        if protocol == "journal":
            text = self._format_journal_entry(entry)
        elif protocol == "mirage":
            text = self._format_mirage_entry(entry)
        else:
            text = json.dumps(entry)

        # Search for similar
        return self.search(text, protocol=protocol, top_k=top_k + 1)[1:]  # Exclude self

    def add_convergence_insight(self, insight: Dict):
        """Add a convergence analysis insight"""

        text = f"""
        Convergence insight: {insight.get('title', '')}
        Protocols involved: {', '.join(insight.get('protocols', []))}
        Key finding: {insight.get('finding', '')}
        Recommendation: {insight.get('recommendation', '')}
        Confidence: {insight.get('confidence', 0)}
        """

        doc_id = hashlib.sha256(
            f"convergence:{insight.get('title', '')}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        embedding = self.embedding_model.encode(text).tolist()

        self.collections["convergence"].add(
            embeddings=[embedding],
            documents=[text],
            metadatas=[
                {
                    "type": "convergence_insight",
                    "protocols": json.dumps(insight.get("protocols", [])),
                    "confidence": insight.get("confidence", 0),
                    "timestamp": datetime.now().isoformat(),
                }
            ],
            ids=[doc_id],
        )

    def get_collection_stats(self) -> Dict:
        """Get statistics about stored data"""

        stats = {}
        for name, collection in self.collections.items():
            count = collection.count()
            stats[name] = {"count": count, "name": name}

        return stats
