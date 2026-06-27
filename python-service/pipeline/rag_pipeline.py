import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from ingestion.vector_store import query_similar

load_dotenv()

# ─── LLM Init ─────────────────────────────────────────────────
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.2,
    groq_api_key=os.getenv("GROQ_API_KEY"),
    request_timeout=25
)


# ─── Step 1: Retrieve relevant context from ChromaDB ──────────
def retrieve_context(diff_text: str) -> list[dict]:
    """
    Query ChromaDB for the top 5 code chunks most similar
    to the incoming PR diff. These chunks represent the
    existing codebase patterns the LLM should compare against.
    """
    results = query_similar(diff_text, n_results=5)
    return results


# ─── Step 2: Format context chunks into readable string ───────
def format_context(chunks: list[dict]) -> str:
    """
    Convert retrieved chunks into a readable string
    to inject into the system prompt.
    """
    if not chunks:
        return "No existing codebase context found."

    formatted = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk["metadata"]
        score = round(chunk["similarity_score"], 3)
        formatted.append(
            f"--- Context Chunk {i} ---\n"
            f"File: {meta['filename']} (lines {meta['start_line']}–{meta['end_line']})\n"
            f"Language: {meta['language']} | Similarity: {score}\n\n"
            f"{chunk['content']}"
        )

    return "\n\n".join(formatted)


# ─── Step 3: Build the prompt ─────────────────────────────────
def build_prompt(diff_text: str, context_str: str) -> list:
    """
    Construct the LangChain message list with system prompt
    and the human message containing diff + context.
    """

    system_prompt = """You are a senior software architect conducting a pull request review.
Your job is to evaluate whether the incoming code changes are consistent with the existing codebase architecture and engineering standards.

You will be given:
1. EXISTING CODEBASE CONTEXT — relevant code chunks from the current codebase retrieved via semantic search
2. PR DIFF — the exact lines being added or changed in this pull request

You must check the PR diff for the following issues:
- Architectural drift: does the new code follow the same patterns, abstractions, and structure as the existing codebase?
- Async anti-patterns: blocking synchronous calls inside async functions, missing await keywords, unhandled promise rejections
- Improper error handling: missing try/catch blocks, swallowed errors, no logging on failures
- Naming convention violations: inconsistent variable, function, or class naming compared to the existing codebase
- Security issues: hardcoded secrets, SQL injection risks, unvalidated inputs, exposed sensitive data

RESPONSE FORMAT — you must respond ONLY using this exact markdown structure, no exceptions:

## Summary
A 2-3 sentence overview of what this PR does and your overall assessment.

## Issues Found
List each issue in this format:
- **[severity]** `filename` — description of the issue

Severity must be one of: critical, high, medium, low
If no issues are found, write: - **[low]** No significant issues found. This PR looks clean.

## Recommendations
- Bullet point list of specific, actionable suggestions for the author.

Do not add any text outside these three sections. Do not add introductions or sign-offs."""

    human_message = f"""EXISTING CODEBASE CONTEXT:
{context_str}

PR DIFF:
{diff_text}

Please review the PR diff against the codebase context and respond in the exact format specified."""

    return [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_message)
    ]


# ─── Step 4: Parse severity from review text ──────────────────
def extract_severity(review_markdown: str) -> str:
    """
    Scan the review text for the highest severity label
    and return it as the overall PR severity.
    """
    if "**[critical]**" in review_markdown:
        return "critical"
    elif "**[high]**" in review_markdown:
        return "high"
    elif "**[medium]**" in review_markdown:
        return "medium"
    else:
        return "low"


# ─── Step 5: Extract flags from review text ───────────────────
def extract_flags(review_markdown: str) -> list[str]:
    """
    Scan the review text for known issue keywords
    and return a list of machine-readable flag strings.
    """
    flags = []
    text = review_markdown.lower()

    flag_map = {
        "blocking-sync-call":      ["blocking", "synchronous", "sync call"],
        "missing-error-handling":  ["try/catch", "error handling", "unhandled"],
        "architectural-drift":     ["architectural drift", "pattern", "abstraction"],
        "naming-convention":       ["naming", "convention", "inconsistent name"],
        "security-issue":          ["hardcoded", "injection", "sensitive", "secret"],
        "missing-await":           ["missing await", "unhandled promise"],
    }

    for flag, keywords in flag_map.items():
        if any(keyword in text for keyword in keywords):
            flags.append(flag)

    if not flags:
        flags.append("no-issues-found")

    return flags


# ─── Step 6: Validate LLM response format ─────────────────────
def validate_response_format(review_markdown: str) -> bool:
    """
    Check that the LLM followed the required markdown structure.
    """
    required_sections = ["## Summary", "## Issues Found", "## Recommendations"]
    return all(section in review_markdown for section in required_sections)


# ─── Main Entry Point ─────────────────────────────────────────
def run_analysis(pr_data: dict) -> dict:
    """
    Full RAG pipeline:
    1. Retrieve relevant context from ChromaDB
    2. Build prompt with context + diff
    3. Call LLM for review
    4. Validate and parse response
    5. Return structured result
    """
    diff_text   = pr_data.get("diff_text", "")
    pr_id       = pr_data.get("pr_id")
    author      = pr_data.get("author", "unknown")
    repo_name   = pr_data.get("repo_name", "unknown")

    print(f"\n[RAG] Starting analysis for PR #{pr_id} by {author} on {repo_name}")

    # ── 1. Retrieve context ──
    print("[RAG] Querying ChromaDB for relevant context...")
    chunks = retrieve_context(diff_text)
    print(f"[RAG] Retrieved {len(chunks)} context chunks")

    # ── 2. Format context ──
    context_str = format_context(chunks)

    # ── 3. Build prompt ──
    messages = build_prompt(diff_text, context_str)

    # ── 4. Call LLM ──
    print("[RAG] Calling LLM for review...")
    response = llm.invoke(messages)
    review_markdown = response.content.strip()
    print("[RAG] LLM response received")

    # ── 5. Validate format — retry once if malformed ──
    if not validate_response_format(review_markdown):
        print("[RAG] Response format invalid — retrying with correction prompt...")
        correction = HumanMessage(
            content="Your previous response did not follow the required format. "
                    "Please rewrite your review using exactly these three sections: "
                    "## Summary, ## Issues Found, ## Recommendations"
        )
        messages.append(response)
        messages.append(correction)
        response = llm.invoke(messages)
        review_markdown = response.content.strip()

    # ── 6. Extract metadata ──
    severity = extract_severity(review_markdown)
    flags    = extract_flags(review_markdown)

    print(f"[RAG] Analysis complete — severity: {severity}, flags: {flags}")

    return {
        "review_markdown": review_markdown,
        "severity":        severity,
        "flags":           flags
    }