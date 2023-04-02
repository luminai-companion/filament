#!/usr/bin/env python3

import argparse
import time

import pandas as pd

import app.memory as memory

pd.set_option("display.max_colwidth", None)

parser = argparse.ArgumentParser()
parser.add_argument("filename")
args = parser.parse_args()

start = time.perf_counter()
memory_book = memory.load_memory_book_file(args.filename)
elapsed = time.perf_counter() - start

num_memories = len(memory_book["entries"])

print(f"{num_memories} memories loaded in {round(elapsed, 4)} s")

memory_book_id = "memory_chat"

start = time.perf_counter()
memory.embed_memories(memory_book_id, memory_book)
elapsed = time.perf_counter() - start

print(f"{num_memories} memories embedded in {round(elapsed, 4)} s")

while True:
    query = input("\nQuery: ")

    start = time.perf_counter()
    memories_df = memory.retrieve_memories(memory_book_id, [query], num_memories)
    elapsed = time.perf_counter() - start

    print(f"\n{memories_df.shape[0]} memories retrieved in {round(elapsed, 4)} s")
    print("Retrieved memories:")
    print(memories_df[["dist", "entry"]])
