import json
import time
import random
from google import genai
from google.genai import types
from .config import get_config

class Generator:
    def __init__(self):
        config = get_config()
        self.client = genai.Client(api_key=config.api_key)
        self.model_name = config.model_name

    def _call_with_retry(self, func, *args, **kwargs):
        """Executes a function with exponential backoff retry logic."""
        max_retries = 5
        base_delay = 2
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Check for rate limit errors (often 429)
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    delay = base_delay ** attempt + random.uniform(0, 1)
                    print(f"⚠️ Rate limit hit. Retrying in {delay:.2f}s... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                else:
                    # For other errors, we might want to retry too if they are transient
                    if attempt < max_retries - 1:
                        delay = base_delay ** attempt + random.uniform(0, 1)
                        print(f"⚠️ API error: {e}. Retrying in {delay:.2f}s... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                    else:
                        raise e
        return None

    def generate_blueprint(self, user_prompt, existing_structure=None):
        prompt = f"""
        You are a senior software architect. Based on the user requirements, generate a project blueprint.

        IMPORTANT:
        1. Explicitly include necessary ecosystem files (e.g., requirements.txt, package.json, README.md, .gitignore, etc.).
        2. Ensure the structure is modular and follows best practices for the chosen language/framework.

        The blueprint should be a JSON object with the following structure:
        {{
          "project_name": "name",
          "files": [
            {{"path": "folder/file.py", "description": "Short description of the file's purpose"}}
          ]
        }}

        User Requirements: {user_prompt}

        {f"Existing Structure: {json.dumps(existing_structure)}" if existing_structure else ""}

        Respond ONLY with the JSON object.
        """

        response = self._call_with_retry(
            self.client.models.generate_content,
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
            )
        )
        return json.loads(response.text)

    def generate_file_content(self, file_path, description, blueprint, context_files):
        # Limit context to avoid exceeding token limits, although 1M is huge.
        # We'll just pass all for now as per user request.
        context_str = "\n".join([f"File: {path}\nContent:\n{content}\n---" for path, content in context_files.items()])

        prompt = f"""
        You are a senior software engineer. Write the full, production-ready source code for the following file.

        Project Blueprint: {json.dumps(blueprint)}

        File to generate: {file_path}
        Description: {description}

        Current Project Context:
        {context_str}

        Provide only the source code for {file_path}. Do not include any markdown formatting or explanations.
        """

        response = self._call_with_retry(
            self.client.models.generate_content,
            model=self.model_name,
            contents=prompt
        )

        content = response.text.strip()
        # Clean up markdown code blocks if the model included them
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines).strip()

        return content
