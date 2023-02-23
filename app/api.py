from collections import defaultdict

from fastapi import Body, FastAPI, Request
from starlette.responses import RedirectResponse, JSONResponse
import httpx
import spacy
import srsly

from app.models import (
    ENT_PROP_MAP,
    RecordsRequest,
    RecordsResponse,
    RecordsEntitiesByTypeResponse,
)
from app.spacy_extractor import SpacyExtractor


app = FastAPI(
    title="KoboldAI Interceptor",
    version="1.0",
    description="Request/response interception proof-of-concept",
)

example_request = srsly.read_json("app/data/example_request.json")

nlp = spacy.load("en_core_web_sm")
extractor = SpacyExtractor(nlp)

kobold_url = "http://127.0.0.1:5000/api"


@app.get("/", include_in_schema=False)
def docs_redirect() -> RedirectResponse:
    return RedirectResponse("/docs")


@app.get("/api/{path:path}")
def handle_get(request: Request, path: str) -> JSONResponse:
    url = f"{kobold_url}/{path}"
    r = httpx.get(url)
    return JSONResponse(status_code=r.status_code, content=r.text)


@app.post("/entities", response_model=RecordsResponse, tags=["NER"])
async def extract_entities(body: RecordsRequest = Body(..., example=example_request)) -> dict:
    """Extract Named Entities from a batch of Records."""

    documents = ({"id": val.recordId, "text": val.data.text} for val in body.values)
    extracted_entities = extractor.extract_entities(documents)

    result = [
        {"recordId": er["id"], "data": {"entities": er["entities"]}} for er in extracted_entities
    ]

    return {"values": result}


@app.post("/entities_by_type", response_model=RecordsEntitiesByTypeResponse, tags=["NER"])
async def extract_entities_by_type(
    body: RecordsRequest = Body(..., example=example_request)
) -> dict:
    """Extract Named Entities from a batch of Records separated by entity label.
    This route can be used directly as a Cognitive Skill in Azure Search
    For Documentation on integration with Azure Search, see here:
    https://docs.microsoft.com/en-us/azure/search/cognitive-search-custom-skill-interface
    """

    documents = ({"id": val.recordId, "text": val.data.text} for val in body.values)
    extracted_entities = extractor.extract_entities(documents)

    result = []
    for er in extracted_entities:
        groupby = defaultdict(list)
        for ent in er["entities"]:
            ent_prop = ENT_PROP_MAP[ent["label"]]
            groupby[ent_prop].append(ent["name"])
        record = {"recordId": er["id"], "data": groupby}
        result.append(record)

    return {"values": result}
