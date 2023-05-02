from fastapi import Body, FastAPI
from starlette.responses import JSONResponse, RedirectResponse, Response

from app import memory

app = FastAPI(
    title="LuminAI filament",
    version="0.1.0",
    description="Services for the LuminAI companion",
)


@app.get("/", include_in_schema=False)
def docs_redirect() -> RedirectResponse:
    return RedirectResponse("/docs")


# TODO should eventually do this asynchronously. redis for queueing?
@app.post("/api/memory/{memory_book_id}/embed")
def handle_memory_embed(memory_book_id: str, payload: dict = Body(...)) -> JSONResponse:
    memory_book = payload["memory_book"]

    if not memory.embed_memories(memory_book_id, memory_book):
        return JSONResponse({"status": "embedding error"}, status_code=500)

    return JSONResponse({"status": "OK"}, status_code=200)


@app.head("/api/memory/{memory_book_id}")
def handle_memory_check(memory_book_id: str) -> JSONResponse:
    if not memory.check_embedding(memory_book_id):
        return Response(status_code=404)

    return Response(status_code=200)


@app.post("/api/memory/{memory_book_id}/prompt")
def handle_memory_prompt(
    memory_book_id: str, payload: dict = Body(...)
) -> JSONResponse:
    if not memory.check_embedding(memory_book_id):
        return JSONResponse({"status": "memory book not found"}, status_code=404)

    prompts = payload["prompt"]
    num_memories_per_sentence = payload["num_memories_per_sentence"]

    memories_df = memory.retrieve_memories(
        memory_book_id, prompts, num_memories_per_sentence
    )

    if memories_df.shape[0] == 0:
        return JSONResponse({"status": "no memories retrieved"}, status_code=404)

    return JSONResponse(memories_df.to_dict(orient="records"), status_code=200)
