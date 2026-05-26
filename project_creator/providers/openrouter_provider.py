import os
from openai import OpenAI

class OpenRouterProvider:
    def __init__(self, api_key):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
        self.fallback_model = "openai/gpt-4.1" # User mention gpt-4.1, likely 4o or similar

    def generate(self, prompt, system_prompt=None, use_fallback=False):
        model = self.fallback_model if use_fallback else self.model
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        completion = self.client.chat.completions.create(
            model=model,
            messages=messages
        )
        return completion.choices[0].message.content
