import os
import getpass

class Config:
    def __init__(self):
        # Gemini 2.5 Flash is primary for this project
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            print("Gemini API Key missing.")
            # self.api_key = getpass.getpass("API Key: ")

        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.chatgpt_cookies_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "browser", "cookies.json")

def get_config(): return Config()
def get_extended_config(): return get_config()
