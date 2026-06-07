import json
import time
import random
import os
from google import genai
from google.genai import types
from project_creator.core.config import get_config

class GeminiProvider:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.config = get_config()
        self.model_name = self.config.gemini_model

    def generate(self, prompt, system_prompt=None, response_mime_type=None, image_bytes=None, image_mime="image/png"):
        parts = []
        if system_prompt:
            parts.append(system_prompt)

        if image_bytes:
            parts.append(types.Part.from_bytes(data=image_bytes, mime_type=image_mime))

        parts.append(prompt)

        config_args = {}
        if response_mime_type:
            config_args['response_mime_type'] = response_mime_type

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=parts,
            config=types.GenerateContentConfig(**config_args) if config_args else None
        )
        return response.text.strip()
