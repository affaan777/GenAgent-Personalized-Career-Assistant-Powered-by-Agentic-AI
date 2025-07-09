"""
Shared configuration for GenAgent full-stack application
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
CHAT_DIR = BASE_DIR / "chat"
STATIC_DIR = BASE_DIR / "static"

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))

# Frontend Configuration
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))
STREAMLIT_HOST = os.getenv("STREAMLIT_HOST", "0.0.0.0")

# Chat Configuration
CHAINLIT_PORT = int(os.getenv("CHAINLIT_PORT", "8502"))
CHAINLIT_HOST = os.getenv("CHAINLIT_HOST", "0.0.0.0")

# Backend Configuration
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")

# File upload settings
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10")) * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.pdf', '.zip'}
UPLOAD_DIR = STATIC_DIR / "resumes"

# Database settings
FAISS_INDEX_PATH = BASE_DIR / "faiss_index.bin"
FAISS_CORPUS_PATH = BASE_DIR / "faiss_corpus.pkl"

# LLM Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_ID = os.getenv("MODEL_ID", "mistralai/mistral-small-3.2-24b-instruct:free")
LOCAL_MODEL_PATH = os.getenv("LOCAL_MODEL_PATH", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")

# Processing settings
PROCESSING_TIMEOUT = int(os.getenv("PROCESSING_TIMEOUT", "300"))  # 5 minutes
MAX_SIMILAR_RESUMES = int(os.getenv("MAX_SIMILAR_RESUMES", "5"))

# UI Configuration
APP_TITLE = "GenAgent - Intelligent Career Assistant"
APP_ICON = "🧠"
THEME_COLOR = "#1f77b4"

# Feature flags
ENABLE_CHAT = os.getenv("ENABLE_CHAT", "true").lower() == "true"
ENABLE_STREAMLIT = os.getenv("ENABLE_STREAMLIT", "true").lower() == "true"
ENABLE_LOCAL_LLM = os.getenv("ENABLE_LOCAL_LLM", "true").lower() == "true"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Security
CORS_ORIGINS = [
    "http://localhost:8501",  # Streamlit
    "http://localhost:8502",  # Chainlit
    "http://127.0.0.1:8501",
    "http://127.0.0.1:8502",
]

# Development settings
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
RELOAD = os.getenv("RELOAD", "true").lower() == "true"

def get_api_url(endpoint: str = "") -> str:
    """Get full API URL for an endpoint"""
    return f"{API_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"

def ensure_directories():
    """Ensure all required directories exist"""
    directories = [FRONTEND_DIR, CHAT_DIR, STATIC_DIR, UPLOAD_DIR]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# Initialize directories
ensure_directories() 