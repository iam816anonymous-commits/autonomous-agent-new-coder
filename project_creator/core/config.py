import os
import getpass

class Config:
    def __init__(self):
        # API Keys
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            print("Gemini API Key not found in environment variables.")
            # Fallback to interactive prompt as requested
            self.api_key = getpass.getpass("Please enter your Gemini API Key: ")

        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

        # Model Names
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")

        # Paths
        self.chatgpt_cookies_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "browser", "cookies.json")

config = None

def get_config():
    global config
    if config is None:
        config = Config()
    return config

def get_extended_config():
    return get_config()
