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

    conn = db.get_connection()
    cur = conn.cursor()

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
        conn,
        if_exists="append",
        index=False,
    )

    conn.commit()

    # memories aren't coming in from agnai with enabled = 1
    # memories = memories_df.loc[memories_df["enabled"]]["entry"].tolist()
    memories = memories_df["entry"].tolist()

    idx = build_index(memories)
    idx_filename = f"{config.ai_data_dir}/{memory_book_id}.ann"
    idx.save(idx_filename)

    return True


def load_memory_book_file(filename: str) -> dict:
    with open(filename, "r") as f:
        memory_book = json.load(f)

    return memory_book


def load_memory_book(memory_book_id: str) -> tuple[pd.DataFrame, AnnoyIndex]:
    conn = db.get_connection()

    memories_df = pd.read_sql(
        "select * from memories where memory_book_id = :id",  # and enabled = 1
        conn,
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
    memory_book_df, idx = load_memory_book(memory_book_id)

    # TODO sentencizing will get weird with actions in asterisks
    # sentences = tokenize_prompts(prompts)
    sentences = prompts
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

    memories_df = memory_book_df.merge(neighbors_df, on="memory_id").sort_values("dist")

    return memories_df
