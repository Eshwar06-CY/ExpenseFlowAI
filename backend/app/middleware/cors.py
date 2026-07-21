import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS policies for the FastAPI application.
    Reads allowed origins from CORS_ORIGINS environment variable (comma-separated),
    with fallback to localhost development defaults.
    """
    env_origins = os.environ.get("CORS_ORIGINS", "")
    if env_origins:
        origins = [o.strip() for o in env_origins.split(",") if o.strip()]
    else:
        origins = [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
