from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb

            client = chromadb.Client()

            self._collection = client.get_or_create_collection(
                name=self._collection_name
            )

            self._use_chroma = True

        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        return {
            "id": str(self._next_index),
            "content": doc.content,
            "embedding": self._embedding_fn(doc.content),
            "metadata": {
                **getattr(doc, "metadata", {}),
                "doc_id": getattr(doc, "id", None),
            },
        }
    
    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        query_embedding = self._embedding_fn(query)

        scored = []

        for record in records:
            score = _dot(
                query_embedding,
                record["embedding"],
            )

            scored.append(
                {
                    **record,
                    "score": score,
                }
            )

        scored.sort(
            key=lambda x: x["score"],
            reverse=True,
        )

        return scored[:top_k]

    
    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        records = []

        for doc in docs:
            record = self._make_record(doc)
            records.append(record)
            self._next_index += 1

        if self._use_chroma and self._collection:
            self._collection.add(
                ids=[r["id"] for r in records],
                documents=[r["content"] for r in records],
                embeddings=[r["embedding"] for r in records],
                metadatas=[r["metadata"] for r in records],
            )

        else:
            self._store.extend(records)


    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if self._use_chroma and self._collection:

            result = self._collection.query(
                query_embeddings=[
                    self._embedding_fn(query)
                ],
                n_results=top_k,
            )

            output = []

            for i, content in enumerate(result["documents"][0]):
                output.append(
                    {
                        "content": content,
                        "metadata": result["metadatas"][0][i],
                        "score": result["distances"][0][i],
                    }
                )

            return output

        return self._search_records(
            query,
            self._store,
            top_k,
        )

    
    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection:
            return self._collection.count()

        return len(self._store)

    
    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self.search(query, top_k)

        filtered = []

        for record in self._store:
            metadata = record.get("metadata", {})

            matched = all(
                metadata.get(key) == value
                for key, value in metadata_filter.items()
            )

            if matched:
                filtered.append(record)

        return self._search_records(
            query,
            filtered,
            top_k,
        )

    
    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma and self._collection:
            records = self._collection.get()

            ids_to_delete = []

            for idx, metadata in enumerate(records["metadatas"]):
                if metadata.get("doc_id") == doc_id:
                    ids_to_delete.append(records["ids"][idx])

            if ids_to_delete:
                self._collection.delete(
                    ids=ids_to_delete
                )
                return True

            return False

        before = len(self._store)

        self._store = [
            record
            for record in self._store
            if record.get("metadata", {}).get("doc_id") != doc_id
        ]

        return len(self._store) < before