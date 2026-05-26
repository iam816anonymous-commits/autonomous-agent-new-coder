import json
import time
import random
import os
from google import genai
from google.genai import types

class GeminiProvider:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")

    def generate(self, prompt, system_prompt=None, response_mime_type=None):
        contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        config_args = {}
        if response_mime_type:
            config_args['response_mime_type'] = response_mime_type

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=types.GenerateContentConfig(**config_args) if config_args else None
        )
        return response.text.strip()
