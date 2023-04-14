# LuminAI filament

filament is a set of services that can be integrated into a front-end to provide special
behavior specific to the LuminAI Companion.

Implemented features:
- Long-term memory semantic recall
- ... that's it so far :)

---

## Resources

Dev requirements:
- Python 3.10 (tested with Python 3.10.10) (you might like pyenv)
- poetry 1.4.1

Install dependencies with poetry:

``` sh
poetry env use 3.10
poetry install
```

After installing dependencies, you'll also need to download the spaCy
language model:

``` sh
poetry run spacy download en_core_web_sm
```

There's a `.env.example` file in the repo that you should copy to `.env` and adjust the
path of `AI_DATA_DIR` to point at a directory where you'd like filament to store data.

To run the service:

``` sh
poetry run python3 main.py
```

Note that the service will take a little while to start up while it downloads
models from Hugging Face. By default the service runs on port 9000.


## Docker image

There's also a Dockerfile if you'd like to build the service as a Docker image.

``` sh
docker build . -t filament:dev
docker run -p 9000:9000 filament:dev
```

Note that the Docker container will take a little while to start up while it downloads
models from Hugging Face.


## Services

### Long-term memory semantic recall

There are three endpoints that support long-term memory. In the following,
`memory_book_id` is assumed to be a guid or something similarly unique per memory book.

- ```POST /api/memory/{memory_book_id}/embed```

This endpoint accepts a json object like `{"memory_book": {...}}` where the `...` is the
same shape json as your memory book exports an agn-ai memory book export. Currently this
endpoint is synchronous and may take a few seconds to embed the memories depending on
the size of the memory book (on an M1 MacBook Air, on the order of 5 seconds for 300
memories).

- ```HEAD /api/memory/{memory_book_id}```

Returns 200 if the book is embedded, 404 if it's not. This will really only matter when
embedding becomes asynchronous, for the purposes of testing if a memory book has been
embedded before attempting recall.

- ```POST /api/memory/{memory_book_id}/prompt```

This endpoint accepts a json object like `{"prompts": [...],
"num_memories_per_sentence": 3}`. `prompts` is an array of strings of however many lines
of prompt context you want to feed in. These lines will be broken up into sentences and
for each sentence the service will try and retrieve `num_memories_per_sentence` memories
from the specified memory book. Retrieved memories will be deduplicated and returned in
sorted order with most relevant memories first. The endpoint returns a json array of
objects containing the following fields:

- `memory_book_id`: a unique id identifying the memory book
- `memory_id`: integer id of the memory within the memory book
- `source`: currently only "book", indicating that the memory came from a memory book
- `entry`: the actual text of the memory
- `priority`: memory priority; see agn-ai memory book documentation
- `weight`: memory weight; see agn-ai memory book documentation
- `enabled`: whether or not the memory is enabled; see agn-ai memory book documentation
- `dist`: minimum L2-normalized Euclidean distance between the prompts and the memory
  (smaller distances indicate greater relevance)

Retrieval is fast: an M1 MacBook Air can retrieve and sort 300 memories for a single
prompt line in less than 100 ms.
