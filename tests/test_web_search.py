import pytest
from fastapi.testclient import TestClient
from project_creator.server import app
from project_creator.providers.gemini_provider import GeminiProvider
from project_creator.core.config import get_config

client = TestClient(app)

def test_search_endpoint():
    # This test will only work if GEMINI_API_KEY is valid
    config = get_config()
    if not config.api_key:
        pytest.skip("GEMINI_API_KEY not set")

    response = client.get("/search/docs?query=fastapi%20documentation")
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "documentation" in data
    assert len(data["documentation"]) > 0

def test_gemini_search_logic():
    config = get_config()
    if not config.api_key:
        pytest.skip("GEMINI_API_KEY not set")

    provider = GeminiProvider(config.api_key)
    result = provider.generate("What is the latest version of FastAPI?", enable_search=True)
    assert isinstance(result, str)
    assert len(result) > 10
