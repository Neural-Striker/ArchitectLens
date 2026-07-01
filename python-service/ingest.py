import sys
import os
from ingestion.code_chunker import chunk_repository
from ingestion.vector_store import ingest_chunks

def main():
    if len(sys.argv) < 2:
        print("Usage: python ingest.py <path_to_repository>")
        print("Example: python ingest.py C:/Users/amazi/Desktop/my-project")
        sys.exit(1)

    repo_path = sys.argv[1]

    if not os.path.isdir(repo_path):
        print(f"Error: '{repo_path}' is not a valid directory.")
        sys.exit(1)

    print(f"\nStarting ingestion for: {repo_path}")
    print("─" * 50)

    print("\nStep 1: Chunking repository...")
    chunks = chunk_repository(repo_path)
    print(f"\nTotal chunks found: {len(chunks)}")

    if not chunks:
        print("No code files found. Check the repo path and supported extensions.")
        sys.exit(1)

    print("\nStep 2: Storing chunks in ChromaDB...")
    ingest_chunks(chunks)

    print("\nDone. Your codebase is now indexed and ready for RAG queries.")

if __name__ == "__main__":
    main()