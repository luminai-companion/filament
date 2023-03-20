import argparse
import time

from annoy import AnnoyIndex
from sentence_transformers import SentenceTransformer

parser = argparse.ArgumentParser()
parser.add_argument("filename")

args = parser.parse_args()

start = time.perf_counter()
model = SentenceTransformer("all-distilroberta-v1")
# model = SentenceTransformer("all-MiniLM-L12-v2")  # best 384 dim

elapsed = time.perf_counter() - start
print(f"Loaded sbert model in {round(elapsed, 4)} s")

with open(args.filename, "r") as f:
    memories = f.read().splitlines()
print(f"Number of memories: {len(memories)}")

start = time.perf_counter()
embeddings = model.encode(memories)
elapsed = time.perf_counter() - start
print(f"Memories embedded in {round(elapsed, 4)} s")

num_features = len(embeddings[0])
print(f"Number of features: {num_features}\n")

idx = AnnoyIndex(num_features, "angular")
# 0 <= sqrt(2-2*cos(u, v)) <= 2, same ordering as cosine distance
# cos = -1, d = sqrt(2 + 2) = 2
# cos = 0, d = sqrt(2) = 1.414
# cos = 1, d = sqrt(2 - 2) = 0

for i, (memory, embedding) in enumerate(zip(memories, embeddings)):
    idx.add_item(i, embedding)
    print(memory)

start = time.perf_counter()
idx.build(100)
elapsed = time.perf_counter() - start
print(f"\nIndex built in {round(elapsed, 4)} s")

start = time.perf_counter()
idx.save(f"{args.filename}.ann")
elapsed = time.perf_counter() - start
print(f"Index saved in {round(elapsed, 4)} s")

start = time.perf_counter()
idx.save(f"{args.filename}.ann")
elapsed = time.perf_counter() - start
print(f"Index loaded in {round(elapsed, 4)} s")

while True:
    query = input("\nQuery: ")
    query_embedding = model.encode([query])[0]

    start = time.perf_counter()
    items, dists = idx.get_nns_by_vector(query_embedding, n=5, include_distances=True)
    elapsed = time.perf_counter() - start
    print(f"Memories retrieved in {round(elapsed, 4)} s")

    print("\nRetrieved memories:")
    for item, dist in zip(items, dists):
        print(f"{round(dist, 3)}: {memories[item]}")
