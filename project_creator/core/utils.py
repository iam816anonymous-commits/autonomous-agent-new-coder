import json
import re

def extract_json(text: str):
    """Resiliently extracts JSON from LLM responses even with markdown or prefix text."""
    if not text: return None

    # 1. Try markdown block extraction
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        clean = match.group(1).strip()
        try:
            return json.loads(clean)
        except:
             # Try fixing common errors like trailing commas before closing braces
             fixed = re.sub(r',\s*([\]}])', r'\1', clean)
             try: return json.loads(fixed)
             except: pass

    # 2. Try finding first { and last }
    try:
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            json_str = text[start:end+1]
            try:
                return json.loads(json_str)
            except:
                fixed = re.sub(r',\s*([\]}])', r'\1', json_str)
                return json.loads(fixed)
    except: pass

    # 3. Final raw fallback
    try:
        return json.loads(text.strip())
    except:
        return None

def sanitize_path(project_root: str, path: str) -> str:
    """Ensures path is safe and within project root."""
    import os
    full_path = os.path.realpath(os.path.abspath(os.path.join(project_root, path)))
    if not full_path.startswith(os.path.realpath(project_root)):
        raise ValueError(f"Security Rejection: Path {path} is outside root {project_root}")
    return full_path

def is_safe_content(content: str) -> bool:
    """Checks for extremely dangerous patterns in generated code."""
    forbidden = [
        r'rm\s+-rf\s+/',
        r'chmod\s+777',
        r'eval\(input\(',
        r'os\.system\('
    ]
    for pattern in forbidden:
        if re.search(pattern, content, re.IGNORECASE):
            return False
    return True
