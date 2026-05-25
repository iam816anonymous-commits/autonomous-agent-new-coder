import os
import getpass

class Config:
    def __init__(self):
        self.api_key = self._get_api_key()
        # The user requested gemini-2.5-flash. Even if 2.0 is the current latest,
        # we will use the user's preferred string, allowing environment override.
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    def _get_api_key(self):
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("Gemini API Key not found in environment variables (GEMINI_API_KEY or GOOGLE_API_KEY).")
            api_key = getpass.getpass("Please enter your Gemini API Key: ")
        return api_key

config = None

def get_config():
    global config
    if config is None:
        config = Config()
    return config
