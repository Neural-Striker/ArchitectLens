import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Literal
from dotenv import load_dotenv
from pipeline.rag_pipeline import run_analysis

load_dotenv()

# ─── Logging Setup ────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ─── App Init ─────────────────────────────────────────────────
app = FastAPI(title="ArchitectLens Python Service")

# ─── CORS Middleware ──────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Auth Middleware ──────────────────────────────────────────
@app.middleware("http")
async def verify_internal_key(request: Request, call_next):
    # Skip auth for these routes
    skip_paths = ["/health", "/docs", "/openapi.json", "/redoc", "/analyze-test"]
    
    if request.url.path in skip_paths:
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
    logger.info(f"Incoming: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

# ─── Pydantic Models ──────────────────────────────────────────
class PRAnalysisRequest(BaseModel):
    pr_id:      int
    repo_name:  str
    diff_text:  str
    author:     str
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
    logger.info(f"Received PR #{request.pr_id} from {request.repo_name} by {request.author}")

    result = run_analysis({
        "pr_id":      request.pr_id,
        "repo_name":  request.repo_name,
        "diff_text":  request.diff_text,
        "author":     request.author,
        "commit_sha": request.commit_sha
    })

    return ReviewResponse(
        review_markdown=result["review_markdown"],
        severity=result["severity"],
        flags=result["flags"]
    )

@app.post("/analyze-test", response_model=ReviewResponse)
async def analyze_pr_test(request: PRAnalysisRequest):
    """Temporary test endpoint — no auth required. Remove before production."""
    logger.info(f"TEST: Received PR #{request.pr_id}")

    result = run_analysis({
        "pr_id":      request.pr_id,
        "repo_name":  request.repo_name,
        "diff_text":  request.diff_text,
        "author":     request.author,
        "commit_sha": request.commit_sha
    })

    return ReviewResponse(
        review_markdown=result["review_markdown"],
        severity=result["severity"],
        flags=result["flags"]
    )