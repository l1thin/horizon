# Horizon - config.py - owned by Dev 3 (AI + Infra)
import os

def load_dotenv(filepath=".env"):
    """Manually parse .env file to avoid external dependencies."""
    if not os.path.exists(filepath):
        return
        
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip(' "\'')

def validate_environment():
    """Ensure required keys are present for the chosen LLM provider."""
    provider = os.environ.get("LLM_PROVIDER", "claude").lower()
    
    if provider == "openai":
        if not os.environ.get("OPENAI_API_KEY"):
            raise EnvironmentError("LLM_PROVIDER is 'openai' but OPENAI_API_KEY is missing from .env.")
    elif provider == "gemini":
        if not os.environ.get("GEMINI_API_KEY"):
            raise EnvironmentError("LLM_PROVIDER is 'gemini' but GEMINI_API_KEY is missing from .env.")
    else:
        # Default claude
        if not os.environ.get("CLAUDE_API_KEY"):
            raise EnvironmentError("LLM_PROVIDER is 'claude' (default) but CLAUDE_API_KEY is missing from .env.")
            
    if not os.environ.get("SUPABASE_URL"):
        print("[Warning] SUPABASE_URL is missing. AI Logging will fail silently.")

# Automatically load and validate on import
load_dotenv()
validate_environment()
