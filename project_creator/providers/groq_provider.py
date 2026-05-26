import os
import json
import time
import random
from groq import Groq

class GroqProvider:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.fallback_model = "mixtral-8x7b-32768"

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
