import re

class LearningConstitution:
    FORBIDDEN_PATTERNS = [
        r'API_KEY\s*=\s*[\'"].*?[\'"]',
        r'PASSWORD\s*=\s*[\'"].*?[\'"]',
        r'SECRET\s*=\s*[\'"].*?[\'"]',
        r'TOKEN\s*=\s*[\'"].*?[\'"]',
        r'ssh-rsa\s+[A-Za-z0-9+/=]+',
        r'DATABASE_URL\s*=\s*[\'"].*?[\'"]',
        r'-----BEGIN\s+PRIVATE\s+KEY-----[\s\S]+?-----END\s+PRIVATE\s+KEY-----',
        r'AKIA[0-9A-Z]{16}', # AWS Access Key ID
        r'amzn\.mws\.[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
        r'sk-[a-zA-Z0-9]{48}', # OpenAI API Key
    ]

    @staticmethod
    def scrub(text: str):
        """Removes sensitive patterns from text before storage."""
        scrubbed = text
        for pattern in LearningConstitution.FORBIDDEN_PATTERNS:
            scrubbed = re.sub(pattern, '[SCRUBBED_BY_CONSTITUTION]', scrubbed, flags=re.IGNORECASE)
        return scrubbed

    @staticmethod
    def is_learnable(path: str):
        """Only allow learning from specific file types and paths."""
        safe_exts = {'.py', '.ts', '.js', '.yaml', '.yml', '.md'}
        _, ext = os.path.splitext(path)
        if ext not in safe_exts: return False

        unsafe_names = {'.env', 'secrets.json', 'tokens.json'}
        if os.path.basename(path) in unsafe_names: return False

        return True
