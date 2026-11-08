"""Uvicorn entry point. Creating the app performs no I/O or background work."""
from app.factory import create_app

app = create_app()
