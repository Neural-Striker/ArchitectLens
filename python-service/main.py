from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="ArchitectLens Python Service")

@app.get("/health")
def health_check():
    return { "status": "ok", "service": "architectlens-python" }