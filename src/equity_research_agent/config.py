import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://equity_user:equity_pass@localhost:5432/equity_research")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")