# ArchitectLens — Internal Service Contract

This document defines the HTTP contract between the Node.js service (Dev 1)
and the FastAPI Python service (Dev 2). Both developers must follow this
exactly. Do not change this file without discussing with your teammate.

---

## Endpoint

**POST** `/analyze`

Called by: Node.js service
Received by: FastAPI Python service

---

## Authentication

Every request from Node.js to FastAPI must include this header:

    X-Internal-Key: <value of INTERNAL_SECRET_KEY in .env>

Both services must have the same value set in their `.env` files.
FastAPI returns `403` if the header is missing or wrong.

---

## Request Body

```json
{
  "pr_id": 42,
  "repo_name": "org/repo-name",
  "diff_text": "diff --git a/index.js...",
  "author": "github-username",
  "commit_sha": "a1b2c3d4e5f6..."
}
```

| Field | Type | Description |
|---|---|---|
| pr_id | number | GitHub PR number |
| repo_name | string | Full repo name e.g. org/repo |
| diff_text | string | Raw unified diff text from GitHub API |
| author | string | GitHub username who opened the PR |
| commit_sha | string | Latest commit hash on the PR |

---

## Success Response

**Status: 200**

```json
{
  "review_markdown": "## Summary\n...\n## Issues Found\n...",
  "severity": "high",
  "flags": [
    "blocking-sync-call",
    "missing-error-handling"
  ]
}
```

| Field | Type | Description |
|---|---|---|
| review_markdown | string | Full review text, formatted in markdown |
| severity | string | One of: `low`, `medium`, `high`, `critical` |
| flags[] | string[] | Machine-readable list of issue types found |

---

## Error Response

**Status: 4xx / 5xx**

```json
{
  "error": "Description of what went wrong",
  "code": 500
}
```

---

## Timeout

Node.js will wait a maximum of **30 seconds** for a response.
FastAPI must respond within this window — even if that means
returning a partial review.

---

## Severity Scale

| Value | Meaning |
|---|---|
| low | Minor style or convention issues |
| medium | Suboptimal patterns, no immediate risk |
| high | Architectural drift or async anti-patterns detected |
| critical | Security issue or breaking change detected |

---

## Flag Values

Agreed list of machine-readable flags FastAPI can return:

| Flag | Meaning |
|---|---|
| `blocking-sync-call` | Synchronous operation inside async context |
| `missing-error-handling` | await call with no try/catch |
| `architectural-drift` | Violates existing codebase patterns |
| `naming-convention` | Naming inconsistent with codebase |
| `security-issue` | Hardcoded secrets, SQL injection risk etc |
| `no-issues-found` | Clean PR, no flags raised |