import json
import os

import pandas as pd
import spacy
from annoy import AnnoyIndex
from sentence_transformers import SentenceTransformer

import app.db as db
from app.config import config

# https://www.sbert.net/docs/pretrained_models.html#sentence-embedding-models
MODEL = SentenceTransformer("all-mpnet-base-v2")
NUM_FEATURES = MODEL.get_sentence_embedding_dimension()

# dot or angular, which is appropriate is based on the sentence transformer used
# https://www.sbert.net/docs/pretrained_models.html#sentence-embedding-models
DISTANCE_METRIC = "angular"
NUM_TREES = 10

NLP = spacy.load("en_core_web_sm")
SENTENCIZER = NLP.add_pipe("sentencizer")


def load_memories_file(filename: str) -> list[str]:
    with open(filename, "r") as f:
        memories = f.read().splitlines()

    return memories


def build_index(memories: list[str]) -> AnnoyIndex:
    embeddings = MODEL.encode(memories)

    idx = AnnoyIndex(NUM_FEATURES, DISTANCE_METRIC)
    for i, embedding in enumerate(embeddings):
        idx.add_item(i, embedding)

    idx.build(NUM_TREES)
    return idx


# IDEA can we compute a distance matrix of memories to find duplicates or near-duplicates?
# IDEA general memory books that can be shared across bots for "interests", like history, art, music
# IDEA chatgpt conversation summaries -> memories?


def check_embedding(memory_book_id: str) -> bool:
    # TODO check db

    idx_filename = f"{config.ai_data_dir}/{memory_book_id}.ann"
    if not os.path.isfile(idx_filename):
        return False

    return True


def embed_memories(memory_book_id: str, memory_book: dict) -> bool:
    memories_df = pd.DataFrame(memory_book["entries"]).drop(
        [
            "name",
            "keywords",
        ],
        axis=1,
    )

    memories_df["memory_book_id"] = memory_book_id
    memories_df["memory_id"] = memories_df.index
    memories_df["source"] = "book"

    cur = db.conn.cursor()

    cur.execute(
        """
insert or replace into memory_books (memory_book_id, source, kind, name, description)
values (?, ?, ?, ?, ?)
        """,
        (
            memory_book_id,
            "agnai",
            memory_book["kind"],
            memory_book["name"],
            memory_book["description"],
        ),
    )

    cur.execute(
        """
delete from memories where memory_book_id = ?
    """,
        (memory_book_id,),
    )

    memories_df.to_sql(
        "memories",
        db.conn,
        if_exists="append",
        index=False,
    )

    db.conn.commit()

    memories = memories_df.loc[memories_df["enabled"]]["entry"].tolist()

    idx = build_index(memories)
    idx_filename = f"{config.ai_data_dir}/{memory_book_id}.ann"
    idx.save(idx_filename)

    return memories_df


def load_memory_book_file(filename: str) -> dict:
    with open(filename, "r") as f:
        memory_book = json.load(f)

    return memory_book


def load_memory_book(memory_book_id: str) -> tuple[pd.DataFrame, AnnoyIndex]:
    memories_df = pd.read_sql(
        "select * from memories where memory_book_id = :id and enabled = 1",
        db.conn,
        params={"id": memory_book_id},
    )

    idx_filename = f"{config.ai_data_dir}/{memory_book_id}.ann"
    idx = AnnoyIndex(NUM_FEATURES, DISTANCE_METRIC)
    idx.load(idx_filename)

    return memories_df, idx


def tokenize_prompts(prompts: list[str]) -> list[str]:
    doc = SENTENCIZER(NLP(" ".join(prompts)))
    sentences = [x.text for x in doc.sents]

    return sentences


def retrieve_memories(
    memory_book_id: str, prompts: list[str], num_memories_per_sentence: int = 3
) -> pd.DataFrame:
    memories_df, idx = load_memory_book(memory_book_id)

    # TODO sentencizing will get weird with actions in asterisks
    sentences = tokenize_prompts(prompts)
    embeddings = MODEL.encode(sentences)

    neighbors_df = pd.DataFrame(columns=["memory_id", "dist"])

    for embedding in embeddings:
        neighbor_ids, dists = idx.get_nns_by_vector(
            embedding, num_memories_per_sentence, include_distances=True
        )

        neighbors_df = pd.concat(
            [neighbors_df, pd.DataFrame({"memory_id": neighbor_ids, "dist": dists})],
            ignore_index=True,
        )

    # eliminate dupes in retrievals by keeping the dupe with the smallest distance
    neighbors_df = (
        neighbors_df.sort_values("dist")
        .groupby("memory_id", sort=False)
        .first()
        .reset_index()
    )

    retrievals_df = memories_df.merge(neighbors_df, on="memory_id").sort_values("dist")

    return retrievals_df
