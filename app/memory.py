import os

import pandas as pd
import spacy
from annoy import AnnoyIndex
from sentence_transformers import SentenceTransformer

from app.config import config

# https://www.sbert.net/docs/pretrained_models.html#sentence-embedding-models
MODEL = SentenceTransformer("all-mpnet-base-v2")
NUM_FEATURES = MODEL.get_sentence_embedding_dimension()

# dot or angular, which is appropriate is based on the sentence transformer used
# https://www.sbert.net/docs/pretrained_models.html#sentence-embedding-models
DISTANCE_METRIC = "angular"

NLP = spacy.load("en_core_web_sm")
SENTENCIZER = NLP.add_pipe("sentencizer")


# TODO memories file CSV for additional fields like priority, weight (eventually SQL)?
def load_memories_txt(filename: str) -> list[str]:
    # TODO error handling
    with open(filename, "r") as f:
        memories = f.read().splitlines()

    return memories


def build_index(memories: list[str]) -> AnnoyIndex:
    embeddings = MODEL.encode(memories)

    idx = AnnoyIndex(NUM_FEATURES, DISTANCE_METRIC)
    for i, embedding in enumerate(embeddings):
        idx.add_item(i, embedding)

    idx.build(20)
    return idx


# IDEA can we compute a distance matrix of memories to find duplicates or near-duplicates?
# IDEA general memory books that can be shared across bots for "interests", like history, art, music
# IDEA chatgpt conversation summaries -> memories?


def check_embedding(memory_book_id: str) -> bool:
    memories_filename = f"{config.ai_data_dir}/{memory_book_id}.txt"
    if not os.path.isfile(memories_filename):
        return False

    idx_filename = f"{config.ai_data_dir}/{memory_book_id}.ann"
    if not os.path.isfile(idx_filename):
        return False

    return True


def embed_memories(memory_book_id: str, memories: list[str]) -> bool:
    memories_filename = f"{config.ai_data_dir}/{memory_book_id}.txt"
    with open(memories_filename, "w") as f:
        f.write("\n".join(memories) + "\n")

    idx = build_index(memories)
    idx_filename = f"{config.ai_data_dir}/{memory_book_id}.ann"
    idx.save(idx_filename)

    return True


def load_memory_book(memory_book_id: str) -> tuple[list[str], AnnoyIndex]:
    memories_filename = f"{config.ai_data_dir}/{memory_book_id}.txt"
    with open(memories_filename, "r") as f:
        memories = f.read().splitlines()

    idx_filename = f"{config.ai_data_dir}/{memory_book_id}.ann"
    idx = AnnoyIndex(NUM_FEATURES, DISTANCE_METRIC)
    idx.load(idx_filename)

    return memories, idx


def tokenize_prompts(prompts: list[str]) -> list[str]:
    doc = SENTENCIZER(NLP(" ".join(prompts)))
    sentences = [x.text for x in doc.sents]

    return sentences


def retrieve_memories(
    memory_book_id: str, prompts: list[str], num_memories_per_sentence: int = 3
) -> pd.DataFrame:
    memories, idx = load_memory_book(memory_book_id)

    sentences = tokenize_prompts(prompts)
    embeddings = MODEL.encode(sentences)

    retrievals_df = pd.DataFrame(columns=["memory_id", "dist"])

    for embedding in embeddings:
        neighbor_ids, dists = idx.get_nns_by_vector(
            embedding, num_memories_per_sentence, include_distances=True
        )

        retrievals_df = pd.concat(
            [retrievals_df, pd.DataFrame({"memory_id": neighbor_ids, "dist": dists})],
            ignore_index=True,
        )

    # eliminate dupes in retrievals by keeping the dupe with the smallest distance
    retrievals_df = (
        retrievals_df.sort_values("dist")
        .groupby("memory_id", sort=False)
        .first()
        .reset_index()
    )

    retrievals_df["memory"] = [memories[i] for i in retrievals_df["memory_id"]]

    return retrievals_df
