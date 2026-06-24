import os

import requests


class OllamaProvider:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")

    def generate(self, prompt, system_prompt=None):
        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\n{prompt}" if system_prompt else prompt,
            "stream": False,
        }
        try:
            response = requests.post(self.base_url, json=payload, timeout=60)
            return response.json().get("response", "").strip()
        except Exception as e:
            print(f"Ollama error: {e}")
            return ""

    def generate_blueprint(self, prompt, system_prompt=None):
        # Local models might need clearer JSON instructions
        full_prompt = f"{system_prompt}\nRespond with JSON only.\n\nTask: {prompt}"
        return self.generate(full_prompt)
