from types import SimpleNamespace
from typing import Union

import emoji
import httpx
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse, RedirectResponse, Response

from app import memory
from app.emoji_predictor import predict_emojis

app = FastAPI(
    title="LuminAI filament",
    version="0.1.0",
    description="Services for the LuminAI companion",
)


@app.get("/", include_in_schema=False)
def docs_redirect() -> RedirectResponse:
    return RedirectResponse("/docs")


@app.get("/api/v1/{path:path}")
def handle_get(
    path: str,
    # TODO need to get this from somewhere for GET/PUT/DELETE requests
    kobold_url: str = "http://127.0.0.1:5000/api/v1",
    q: Union[str, None] = None,
) -> JSONResponse:
    url = f"{kobold_url}/{path}"

    response = httpx.get(url, params=q)
    return JSONResponse(response.json(), status_code=response.status_code)


def trim_response(response_text: str, stop_tokens: list[str]) -> str:
    if not stop_tokens:
        return response_text

    first_match_ind = min(
        list(filter(lambda x: x >= 0, [response_text.find(x) for x in stop_tokens])),
        default=None,
    )

    if first_match_ind is None:
        return response_text

    response_text = response_text[0 : first_match_ind - 1]
    return response_text


def parse_request(request: dict) -> tuple[dict, dict]:
    kobold_url = request.pop("koboldUrl", "http://127.0.0.1:5000") + "/api/v1"
    stop_tokens = request.pop("stopTokens", [])

    params_dict = {"kobold_url": kobold_url, "stop_tokens": stop_tokens}
    params = SimpleNamespace(**params_dict)

    return request, params


def inject_into_prompt(prompt: str, lines: str) -> str:
    ind = prompt.find("<START>")

    if ind >= 0:
        prompt = prompt[:ind] + lines + prompt[ind:]

    return prompt


app.state.memory_fifo = []


def process_generate_request_hooks(request: dict, params: dict) -> str:
    prompt_text = request["prompt"]

    # TODO some number of previous context lines here instead of one line and FIFO?
    last_spoken_line = prompt_text.split("\n")[-2]
    new_memories = memory.retrieve_memories(last_spoken_line, num_memories=3)
    print(f"new_memories: {new_memories}")

    # IDEA rather than a strict queue, maintain a priority queue with cosine distances?
    memory_fifo = new_memories
    memory_fifo.extend(x for x in app.state.memory_fifo if x not in memory_fifo)

    memory_fifo = memory_fifo[0:13]
    print(f"memory_fifo: {memory_fifo}")

    memories_str = "[ Facts: " + "; ".join(memory_fifo) + " ]\n"
    prompt_text = inject_into_prompt(prompt_text, memories_str)

    app.state.memory_fifo = memory_fifo

    request["prompt"] = prompt_text
    return request


def process_generate_response_hooks(response: dict, params: dict) -> dict:
    response_text = trim_response(response["results"][0]["text"], params.stop_tokens)

    # TODO disabled for memory testing
    # detect if there's already an emoji in the response and skip prediction if there is
    # if emoji.emoji_count(response_text) == 0:
    #     predicted_emoji = predict_emojis(response_text, k=1)
    #     response_text += f" {predicted_emoji}"

    response["results"][0]["text"] = response_text
    return response


@app.post("/api/v1/generate")
async def handle_generate(request: Request) -> JSONResponse:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    payload_in, params = parse_request(await request.json())
    payload = process_generate_request_hooks(payload_in, params)

    # TODO could make this async with httpx
    post_response = httpx.post(
        f"{params.kobold_url}/generate", headers=headers, json=payload, timeout=120
    )

    response = process_generate_response_hooks(post_response.json(), params)
    return JSONResponse(response, status_code=post_response.status_code)


# TODO should eventually do this asynchronously. redis for queueing?
@app.post("/api/memory/{memory_book_id}/embed")
async def handle_memory_embed(memory_book_id: str, request: Request) -> JSONResponse:
    payload = await request.json()
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
async def handle_memory_prompt(memory_book_id: str, request: Request) -> JSONResponse:
    if not memory.check_embedding(memory_book_id):
        return JSONResponse({"status": "memory book not found"}, status_code=404)

    payload = await request.json()
    prompts = payload["prompts"]
    num_memories_per_sentence = payload["num_memories_per_sentence"]

    memories_df = memory.retrieve_memories(
        memory_book_id, prompts, num_memories_per_sentence
    )

    if memories_df.shape[0] == 0:
        return JSONResponse({"status": "no memories retrieved"}, status_code=404)

    return JSONResponse(memories_df.to_dict(orient="records"), status_code=200)
