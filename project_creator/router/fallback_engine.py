import time
import random

class FallbackEngine:
    def __init__(self, providers):
        self.providers = providers

    def execute_with_fallback(self, prompt, system_prompt=None, response_mime_type=None):
        last_error = None
        for provider in self.providers:
            # Implement retry logic for EACH provider before falling back to the next
            max_retries = 3
            base_delay = 2

            for attempt in range(max_retries):
                try:
                    if hasattr(provider, 'generate'):
                        # Pass response_mime_type if the provider supports it
                        if response_mime_type and provider.__class__.__name__ == "GeminiProvider":
                            return provider.generate(prompt, system_prompt, response_mime_type=response_mime_type)
                        return provider.generate(prompt, system_prompt)
                except Exception as e:
                    error_str = str(e)
                    # Check for rate limit or transient errors
                    is_rate_limit = "429" in error_str or "RESOURCE_EXHAUSTED" in error_str

                    if is_rate_limit and attempt < max_retries - 1:
                        delay = base_delay ** attempt + random.uniform(0, 1)
                        print(f"⚠️ Rate limit for {provider.__class__.__name__}. Retrying in {delay:.2f}s... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                        continue

                    print(f"⚠️ Provider {provider.__class__.__name__} failed: {error_str}")
                    last_error = e
                    break # Move to next provider

        raise Exception(f"All providers and retries failed. Last error: {last_error}")
