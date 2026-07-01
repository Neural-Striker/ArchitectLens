import os
import re

# ─── Config ───────────────────────────────────────────────────
SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".java"}

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", "dist",
    "build", "venv", ".venv", ".idea", ".vscode"
}

SKIP_FILE_PATTERNS = [
    r".*\.lock$",
    r".*\.min\.js$",
    r".*\.map$",
]

# ─── Boundary Patterns per Language ───────────────────────────
# These regex patterns detect the START of a new function/class
BOUNDARY_PATTERNS = {
    ".py": re.compile(r"^(def |class )", re.MULTILINE),
    ".js": re.compile(r"^(function |class |const \w+ = \(|const \w+ = async)", re.MULTILINE),
    ".ts": re.compile(r"^(function |class |const \w+ = \(|const \w+ = async|async function)", re.MULTILINE),
    ".java": re.compile(r"^(\s*(public|private|protected|static).*\()", re.MULTILINE),
}


def should_skip_file(filename: str) -> bool:
    for pattern in SKIP_FILE_PATTERNS:
        if re.match(pattern, filename):
            return True
    return False


def get_language(ext: str) -> str:
    mapping = {".py": "python", ".js": "javascript", ".ts": "typescript", ".java": "java"}
    return mapping.get(ext, "unknown")


def split_into_chunks(content: str, ext: str, filename: str) -> list[dict]:
    """
    Split file content at function/class boundaries.
    Falls back to returning the whole file as one chunk
    if no boundaries are detected.
    """
    pattern = BOUNDARY_PATTERNS.get(ext)
    language = get_language(ext)
    lines = content.splitlines()

    if not pattern:
        # No boundary pattern — return whole file as single chunk
        return [{
            "content": content,
            "filename": filename,
            "start_line": 1,
            "end_line": len(lines),
            "language": language
        }]

    # Find line numbers where each boundary starts
    boundary_lines = []
    for i, line in enumerate(lines):
        if pattern.match(line.strip()):
            boundary_lines.append(i)

    if not boundary_lines:
        # No boundaries found — whole file is one chunk
        return [{
            "content": content,
            "filename": filename,
            "start_line": 1,
            "end_line": len(lines),
            "language": language
        }]

    # Build chunks between boundaries
    chunks = []
    boundary_lines.append(len(lines))  # sentinel — end of file

    for i in range(len(boundary_lines) - 1):
        start = boundary_lines[i]
        end = boundary_lines[i + 1]
        chunk_lines = lines[start:end]
        chunk_content = "\n".join(chunk_lines).strip()

        if not chunk_content:
            continue

        chunks.append({
            "content": chunk_content,
            "filename": filename,
            "start_line": start + 1,   # 1-indexed for readability
            "end_line": end,
            "language": language
        })

    return chunks


def chunk_repository(repo_path: str) -> list[dict]:
    """
    Walk a repository directory tree, read all supported
    code files, and return a flat list of code chunks.
    """
    all_chunks = []

    for root, dirs, files in os.walk(repo_path):
        # Remove skipped directories in-place so os.walk doesn't recurse into them
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for filename in files:
            ext = os.path.splitext(filename)[1]

            if ext not in SUPPORTED_EXTENSIONS:
                continue

            if should_skip_file(filename):
                continue

            filepath = os.path.join(root, filename)
            relative_path = os.path.relpath(filepath, repo_path)

            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                if not content.strip():
                    continue

                chunks = split_into_chunks(content, ext, relative_path)
                all_chunks.extend(chunks)
                print(f"  Chunked: {relative_path} → {len(chunks)} chunk(s)")

            except Exception as e:
                print(f"  Skipped {relative_path}: {e}")

    return all_chunks