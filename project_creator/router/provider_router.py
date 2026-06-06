from project_creator.providers.groq_provider import GroqProvider
from project_creator.providers.gemini_provider import GeminiProvider
from project_creator.providers.openrouter_provider import OpenRouterProvider
from project_creator.providers.chatgpt_browser_provider import ChatGPTBrowserProvider
from project_creator.providers.ollama_provider import OllamaProvider
from .fallback_engine import FallbackEngine
from project_creator.core.config import get_extended_config

class ProviderRouter:
    def __init__(self):
        config = get_extended_config()

        # Priority: Groq -> Gemini -> OpenRouter -> ChatGPT Browser
        self.groq = GroqProvider(config.groq_api_key) if config.groq_api_key else None
        self.gemini = GeminiProvider(config.api_key) if config.api_key else None
        self.openrouter = OpenRouterProvider(config.openrouter_api_key) if config.openrouter_api_key else None
        self.chatgpt = ChatGPTBrowserProvider(config.chatgpt_cookies_path)
        self.ollama = OllamaProvider() # Always available locally if Ollama is running

        self.sequence = [p for p in [self.groq, self.gemini, self.openrouter, self.chatgpt, self.ollama] if p is not None]
        self.fallback_engine = FallbackEngine(self.sequence)

    def generate(self, prompt, system_prompt=None):
        return self.fallback_engine.execute_with_fallback(prompt, system_prompt)

    def generate_blueprint(self, prompt, system_prompt=None):
        # User specified: Gemini is primary for blueprint, ChatGPT and Ollama as fallbacks
        blueprint_sequence = [p for p in [self.gemini, self.chatgpt, self.ollama] if p is not None]
        engine = FallbackEngine(blueprint_sequence)
        return engine.execute_with_fallback(prompt, system_prompt, response_mime_type='application/json')
