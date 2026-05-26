import os
import json
import asyncio
from playwright.async_api import async_playwright

class ChatGPTBrowserProvider:
    def __init__(self, cookies_path):
        self.cookies_path = cookies_path

    async def generate_async(self, prompt):
        async with async_playwright() as p:
            # We use a persistent context to use cookies
            browser_context = await p.chromium.launch_persistent_context(
                user_data_dir="/tmp/chatgpt_browser_data",
                headless=True
            )

            if os.path.exists(self.cookies_path):
                with open(self.cookies_path, 'r') as f:
                    cookies = json.load(f)
                await browser_context.add_cookies(cookies)

            page = await browser_context.new_page()
            await page.goto("https://chatgpt.com")

            # This is a VERY simplified interaction and might be brittle
            # In a real scenario, this needs robust selector handling
            await page.fill('textarea[id="prompt-textarea"]', prompt)
            await page.press('textarea[id="prompt-textarea"]', "Enter")

            # Wait for the response to finish - very heuristic
            await asyncio.sleep(10)

            # Heuristic to find the last message
            last_message_selector = 'div[data-message-author-role="assistant"]'
            last_message = await page.locator(last_message_selector).last.inner_text()

            await browser_context.close()
            return last_message

    def generate(self, prompt, system_prompt=None):
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        return asyncio.run(self.generate_async(full_prompt))
