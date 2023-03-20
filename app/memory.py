from annoy import AnnoyIndex
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-distilroberta-v1")


def load_memories(memories_filename: str) -> list[str]:
    with open(memories_filename, "r") as f:
        memories = f.read().splitlines()

    return memories


def build_index(memories: list[str]) -> AnnoyIndex:
    embeddings = model.encode(memories)
    num_features = len(embeddings[0])
    idx = AnnoyIndex(num_features, "angular")

    for i, (memory, embedding) in enumerate(zip(memories, embeddings)):
        idx.add_item(i, embedding)

    idx.build(100)

    return idx


memories = load_memories("app/AidenMemoryBank")
idx = build_index(memories)


def retrieve_memories(query: str, num_memories: int = 3) -> list[str]:
    embedding = model.encode([query])[0]
    item_ids, dists = idx.get_nns_by_vector(
        embedding, num_memories, include_distances=True
    )

    items = [memories[i] for i in item_ids]
    return items


def retrieve_memories_str(query: str, num_memories: int = 3) -> str:
    items = retrieve_memories(query, num_memories)
    memories_str = "[ Facts: " + "; ".join(items) + " ]"

    return memories_str
