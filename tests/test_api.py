import json

from dotenv import load_dotenv
from starlette.testclient import TestClient

from app.api import app
from app.config import config

load_dotenv()


def load_test_memory_book() -> dict:
    with open(f"{config.ai_data_dir}/aiden_book.json") as f:
        memory_book = json.load(f)

    return memory_book


def test_memory() -> None:
    client = TestClient(app)

    memory_book = load_test_memory_book()
    embed_payload = {"memory_book": memory_book}

    embed_response = client.post("/api/memory/aiden_book/embed", json=embed_payload)
    assert embed_response.status_code == 200
    assert embed_response.json() == {"status": "OK"}

    check_response = client.head("/api/memory/nonexistent")
    assert check_response.status_code == 404

    check_response = client.head("/api/memory/aiden_book")
    assert check_response.status_code == 200

    prompts = ["charity.", "vacation.", "cats."]
    prompt_payload = {"prompts": prompts, "num_memories_per_sentence": 3}

    prompt_response = client.post("/api/memory/aiden_book/prompt", json=prompt_payload)
    assert prompt_response.status_code == 200

    memories = prompt_response.json()
    # TODO this might not always be 9, if retrieval results in duplicates
    assert len(memories) == 9

    # TODO this is going to change if the embedding model or num_trees changes
    memory_ids = [x["memory_id"] for x in memories]
    assert memory_ids == [
        259,
        71,
        268,
        194,
        244,
        84,
        50,
        19,
        126,
    ]
