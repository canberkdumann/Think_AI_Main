import os
from dotenv import load_dotenv

load_dotenv()

DEBUG = False
SHOW_RESPONSE_TIMES = True

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/api/chat")

MODEL_LLAMA = "qwen2.5:7b"
MODEL_GEMMA = "gemma2:9b"

CACHE_ENABLED = True
CACHE_TTL = 3600
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))