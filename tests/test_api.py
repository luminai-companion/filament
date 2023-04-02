import json

from starlette.testclient import TestClient

from app.api import app
from app.config import config


def load_test_memory_book() -> dict:
    with open(f"{config.ai_data_dir}/aiden_book.json") as f:
        memory_book = json.load(f)

    return memory_book


def test_api_embed() -> None:
    client = TestClient(app)

    memory_book = load_test_memory_book()
    payload = {"memory_book": memory_book}

    response = client.post("/api/memory/aiden_book/embed", json=payload)
    assert response.status_code == 200
