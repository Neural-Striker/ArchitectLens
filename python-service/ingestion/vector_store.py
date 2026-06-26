import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

CHROMA_PERSIST_PATH = os.getenv("CHROMA_PERSIST_PATH", "./chroma_db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COLLECTION_NAME = "codebase_context"


def get_collection():
    """
    Initialize a persistent ChromaDB client and return
    the codebase_context collection.
    """
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_PATH)

    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name="text-embedding-3-small"
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=openai_ef,
        metadata={"hnsw:space": "cosine"}  # cosine similarity for code
    )

    return collection


def ingest_chunks(chunks: list[dict]):
    """
    Take a list of code chunks and upsert them into ChromaDB.
    Embeddings are generated automatically via OpenAI.
    """
    collection = get_collection()

    if not chunks:
        print("No chunks to ingest.")
        return

    documents = []
    metadatas = []
    ids = []

    for i, chunk in enumerate(chunks):
        # ID is filename + start line — unique per chunk
        chunk_id = f"{chunk['filename']}::{chunk['start_line']}"

        documents.append(chunk["content"])
        metadatas.append({
            "filename": chunk["filename"],
            "start_line": chunk["start_line"],
            "end_line": chunk["end_line"],
            "language": chunk["language"]
        })
        ids.append(chunk_id)

    # Upsert in batches of 50 to avoid hitting API limits
    batch_size = 50
    total = len(documents)

    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        collection.upsert(
            documents=documents[start:end],
            metadatas=metadatas[start:end],
            ids=ids[start:end]
        )
        print(f"  Upserted batch {start}–{end} of {total}")

    print(f"\nIngestion complete. {total} chunks stored in ChromaDB.")


def query_similar(query_text: str, n_results: int = 5) -> list[dict]:
    """
    Given a query string (e.g. a PR diff), return the most
    semantically similar code chunks from the vector store.
    """
    collection = get_collection()

    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )

    # Flatten and format results
    formatted = []
    for i in range(len(results["documents"][0])):
        formatted.append({
            "content": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "similarity_score": 1 - results["distances"][0][i]  # convert distance to similarity
        })

    return formatted