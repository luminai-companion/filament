from fastapi import FastAPI, Request
from starlette.responses import RedirectResponse, JSONResponse
from typing import Union

import httpx

app = FastAPI(
    title="KoboldAI Interceptor",
    version="1.0",
    description="Request/response interception proof-of-concept",
)

api_url = "http://127.0.0.1:5000/api/v1"

@app.get("/", include_in_schema=False)
def docs_redirect() -> RedirectResponse:
    return RedirectResponse("/docs")


@app.get("/api/v1/{path:path}")
def handle_get(path: str, q: Union[str, None] = None) -> JSONResponse:
    url = f"{api_url}/{path}"
    response = httpx.get(url, params=q)

    return JSONResponse(response.json(), status_code=response.status_code)

@app.post("/api/v1/generate")
async def handle_generate(request: Request) -> JSONResponse:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    payload = await request.json()
    payload["prompt"] = "Once upon a time, "  # example interception

    # TODO could make this async with httpx
    response = httpx.post(
        f"{api_url}/generate",
        headers=headers,
        json=payload
    )

    json_response = JSONResponse(response.json(), status_code=response.status_code)
    return json_response
