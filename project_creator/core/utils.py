import json
import re

def extract_json(text: str):
    """Resiliently extracts JSON from LLM responses even with markdown or prefix text."""
    if not text: return None

    # Try markdown block extraction
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except: pass

    # Try finding first { and last }
    try:
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            return json.loads(text[start:end+1])
    except: pass

    # Final fallback attempt
    try:
        return json.loads(text.strip())
    except:
        return None
