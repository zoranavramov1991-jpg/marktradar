# config.py — MarktRadar OS PRO
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

class Config:
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
    OPENAI_API_KEY     = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_MODEL       = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    OPENROUTER_MODEL   = os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
    USE_MOCK           = os.environ.get("USE_MOCK", "False").lower() == "true"
    DEBUG              = os.environ.get("DEBUG", "False").lower() == "true"
