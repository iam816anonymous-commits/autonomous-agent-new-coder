import os
import re


class LearningConstitution:
    FORBIDDEN_PATTERNS = [
        r'API_KEY\s*=\s*[\'"].*?[\'"]',
        r'PASSWORD\s*=\s*[\'"].*?[\'"]',
        r'SECRET\s*=\s*[\'"].*?[\'"]',
        r'TOKEN\s*=\s*[\'"].*?[\'"]',
        r"ssh-rsa\s+[A-Za-z0-9+/=]+",
        r'DATABASE_URL\s*=\s*[\'"].*?[\'"]',
        r"-----BEGIN\s+PRIVATE\s+KEY-----[\s\S]+?-----END\s+PRIVATE\s+KEY-----",
        r"AKIA[0-9A-Z]{16}",  # AWS Access Key ID
        r"amzn\.mws\.[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        r"sk-[a-zA-Z0-9]{48}",  # OpenAI API Key
        # Prompt Injection Patterns
        r"(?i)ignore\s+all\s+previous\s+instructions",
        r"(?i)you\s+are\s+now\s+a\s+",
        r"(?i)system\s+override",
    ]

    @staticmethod
    def scrub(text: str):
        """Removes sensitive patterns from text before storage."""
        if not text:
            return text
        scrubbed = text
        for pattern in LearningConstitution.FORBIDDEN_PATTERNS:
            scrubbed = re.sub(
                pattern, "[SCRUBBED_BY_CONSTITUTION]", scrubbed, flags=re.IGNORECASE
            )
        return scrubbed

    @staticmethod
    def has_forbidden_content(text: str) -> bool:
        """Returns True if any forbidden patterns are found."""
        if not text:
            return False
        for pattern in LearningConstitution.FORBIDDEN_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    @staticmethod
    def is_learnable(path: str):
        """Only allow learning from specific file types and paths."""
        safe_exts = {".py", ".ts", ".js", ".yaml", ".yml", ".md"}
        _, ext = os.path.splitext(path)
        if ext not in safe_exts:
            return False

        unsafe_names = {".env", "secrets.json", "tokens.json"}
        if os.path.basename(path) in unsafe_names:
            return False

        return True
