"""
ChromaDB persistent vector database client.

Uses PersistentClient with SQLite backend for local storage.
Data survives application restarts.

IMPORTANT: Requires Python 3.11 or 3.12. Python 3.14+ is not yet supported by ChromaDB 1.4.x
due to Pydantic v1 compatibility issues. See: https://github.com/chroma-core/chroma/issues/

Temporary workaround: Mock implementation for Python 3.14 compatibility during development.
Production deployment should use Python 3.11 or 3.12.
"""
import sys
from pathlib import Path
from typing import Optional, Any
import json

# Check Python version and provide clear guidance
PYTHON_VERSION = (sys.version_info.major, sys.version_info.minor)
CHROMA_COMPATIBLE = PYTHON_VERSION < (3, 14)

if not CHROMA_COMPATIBLE:
    print(f"WARNING: Python {PYTHON_VERSION[0]}.{PYTHON_VERSION[1]} detected.")
    print("ChromaDB requires Python 3.11 or 3.12 for production use.")
    print("Using mock implementation for development. Install Python 3.11/3.12 for full functionality.")
    print()

# Try to import chromadb, fall back to mock if incompatible
try:
    if CHROMA_COMPATIBLE:
        import chromadb
        USING_MOCK = False
    else:
        raise ImportError("Python 3.14+ not compatible with ChromaDB 1.4.x")
except (ImportError, Exception) as e:
    USING_MOCK = True
    print(f"ChromaDB import failed: {e}")
    print("Using mock ChromaDB implementation...")

    # Mock ChromaDB classes for development
    class MockCollection:
        def __init__(self, name: str, metadata: dict, persist_path: Path):
            self.name = name
            self.metadata = metadata
            self.persist_path = persist_path
            self._documents = []
            self._load()

        def _load(self):
            """Load persisted documents from JSON file."""
            if self.persist_path.exists():
                try:
                    with open(self.persist_path, 'r') as f:
                        self._documents = json.load(f)
                except Exception:
                    self._documents = []

        def _save(self):
            """Save documents to JSON file."""
            self.persist_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.persist_path, 'w') as f:
                json.dump(self._documents, f, indent=2)

        def add(self, documents: list, metadatas: list, ids: list, embeddings: list = None):
            """Add documents to collection."""
            embeddings = embeddings or [None] * len(documents)
            for doc, meta, id, emb in zip(documents, metadatas, ids, embeddings):
                self._documents.append({
                    'id': id,
                    'document': doc,
                    'metadata': meta,
                    'embedding': emb
                })
            self._save()

        def count(self) -> int:
            """Get number of documents in collection."""
            return len(self._documents)

        def get(self, ids: list = None, limit: int = None, include: list = None) -> dict:
            """Get documents from collection (matches ChromaDB API)."""
            docs = self._documents
            if ids:
                docs = [d for d in docs if d['id'] in ids]
            if limit:
                docs = docs[:limit]

            result = {
                'ids': [d['id'] for d in docs],
                'documents': [d['document'] for d in docs],
                'metadatas': [d['metadata'] for d in docs],
                'embeddings': [d.get('embedding') for d in docs]
            }
            return result

    class MockPersistentClient:
        def __init__(self, path: str):
            self.path = Path(path)
            self.path.mkdir(parents=True, exist_ok=True)
            self._collections = {}

        def get_or_create_collection(self, name: str, metadata: dict = None):
            """Get existing collection or create new one."""
            if name not in self._collections:
                persist_path = self.path / f"{name}.json"
                self._collections[name] = MockCollection(name, metadata or {}, persist_path)
            return self._collections[name]

    # Use mock classes
    chromadb = type('chromadb', (), {
        'PersistentClient': MockPersistentClient
    })

def get_chroma_client(chroma_path: Optional[Path] = None) -> Any:
    """
    Initialize ChromaDB persistent client.

    Args:
        chroma_path: Path to ChromaDB storage directory.
                     Defaults to ./chroma_db relative to project root.

    Returns:
        ChromaDB persistent client with SQLite backend.

    Note:
        Uses PersistentClient (not Client) to ensure data survives restarts.
        See RESEARCH.md Pitfall #2 for why this matters.
    """
    if chroma_path is None:
        # Default: chroma_db/ in project root
        chroma_path = Path(__file__).parent.parent.parent / "chroma_db"

    # Create directory if doesn't exist
    chroma_path.mkdir(exist_ok=True)

    # Create persistent client (SQLite-backed)
    client = chromadb.PersistentClient(path=str(chroma_path))
    return client

def get_or_create_collection(
    client: Any,
    name: str = "system_design_docs"
) -> Any:
    """
    Get existing collection or create new one.

    Args:
        client: ChromaDB persistent client
        name: Collection name (default: system_design_docs)

    Returns:
        ChromaDB collection for storing document chunks

    Note:
        get_or_create_collection is idempotent - safe to call multiple times.
        Collection persists across restarts.
    """
    collection = client.get_or_create_collection(
        name=name,
        metadata={
            "description": "System design interview resources",
            "embedding_model": "all-MiniLM-L6-v2"
        }
    )
    return collection

def verify_persistence() -> bool:
    """
    Verify ChromaDB persistence works (data survives restart).

    Returns:
        True if persistence validated, False otherwise

    Test:
        1. Add test document to collection
        2. Get client again (simulates restart)
        3. Check document still exists
    """
    # First run: add test document
    client = get_chroma_client()
    collection = get_or_create_collection(client, name="persistence_test")

    # Add test document if collection is empty
    if collection.count() == 0:
        collection.add(
            documents=["Test document for persistence validation"],
            metadatas=[{"test": True}],
            ids=["persistence_test_1"]
        )
        print("✓ Added test document to ChromaDB")
        print("  Re-run this script after restart to validate persistence")
        return False
    else:
        # Collection has documents - persistence verified
        print(f"✓ ChromaDB persistence verified: {collection.count()} documents found")
        return True

if __name__ == "__main__":
    # Standalone test
    client = get_chroma_client()
    collection = get_or_create_collection(client)
    print(f"ChromaDB initialized: {collection.count()} documents in collection")

    # Run persistence test
    verify_persistence()
