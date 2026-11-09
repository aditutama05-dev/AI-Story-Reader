"""Vercel ASGI entrypoint for the existing Novelith AI FastAPI backend."""
from backend.app.main import app

# Vercel's Python runtime detects this ASGI application object.
