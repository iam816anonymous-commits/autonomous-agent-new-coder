import os
import getpass

class Config:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            print("Gemini API Key not found in environment variables (GEMINI_API_KEY or GOOGLE_API_KEY).")
            # We will try to get it via input if it's not provided, to be user-friendly as requested
            self.api_key = getpass.getpass("Please enter your Gemini API Key: ")

        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash") # 2.5 flash doesn't exist yet, using 2.0
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.chatgpt_cookies_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "browser", "cookies.json")

config = None

def get_config():
    global config
    if config is None:
        config = Config()
    return config

def get_extended_config():
    return get_config()
