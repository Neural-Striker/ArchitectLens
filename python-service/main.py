import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Literal
from dotenv import load_dotenv

load_dotenv()

# ─── Logging Setup ───────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ─── App Init ────────────────────────────────────────────────
app = FastAPI(title="ArchitectLens Python Service")

# ─── CORS Middleware ─────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Auth Middleware ──────────────────────────────────────────
@app.middleware("http")
async def verify_internal_key(request: Request, call_next):
    # Skip auth check for health endpoint
    if request.url.path == "/health":
        return await call_next(request)

    incoming_key = request.headers.get("X-Internal-Key")
    expected_key = os.getenv("INTERNAL_SECRET_KEY")

    if not incoming_key or incoming_key != expected_key:
        logger.warning(f"Unauthorized request to {request.url.path}")
        return JSONResponse(
            status_code=403,
            content={"error": "Forbidden: invalid or missing X-Internal-Key", "code": 403}
        )

    return await call_next(request)

# ─── Request Logging Middleware ───────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# ─── Pydantic Models ──────────────────────────────────────────
class PRAnalysisRequest(BaseModel):
    pr_id: int
    repo_name: str
    diff_text: str
    author: str
    commit_sha: str

class ReviewResponse(BaseModel):
    review_markdown: str
    severity: Literal["low", "medium", "high", "critical"]
    flags: list[str]

# ─── Routes ───────────────────────────────────────────────────
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "architectlens-python"}


@app.post("/analyze", response_model=ReviewResponse)
async def analyze_pr(request: PRAnalysisRequest):
    logger.info(f"Received PR #{request.pr_id} from repo {request.repo_name} by {request.author}")

    # ── Hardcoded mock response for now ──
    # This gets replaced in Step 1.6 with the real RAG pipeline
    return ReviewResponse(
        review_markdown="""## Summary
Mock review for PR #{pr_id} by {author}. Real analysis coming in Step 1.6.

## Issues Found
- **[medium]** This is a placeholder issue for testing the pipeline end-to-end.

## Recommendations
- Wire up the RAG pipeline in Step 1.6 to replace this mock response.
""".format(pr_id=request.pr_id, author=request.author),
        severity="medium",
        flags=["no-issues-found"]
    )