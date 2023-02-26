# KoboldAI Interceptor

Request/response interception proof-of-concept

---

## Resources
This project has two key dependencies:

| Dependency Name | Documentation                | Description                                                                            |
|-----------------|------------------------------|----------------------------------------------------------------------------------------|
| spaCy           | https://spacy.io             | Industrial-strength Natural Language Processing (NLP) with Python and Cython           |
| FastAPI         | https://fastapi.tiangolo.com | FastAPI framework, high performance, easy to learn, fast to code, ready for production |
---

## Run Locally

Requirements:
- Python 3.10
- Docker
- Node.js

Tested with Python 3.10.10.

Run koboldai/koboldai:united Docker image with port 5000 in the container mapped to port 5000 on your local machine.

Browse to the KoboldAI interface at http://127.0.0.1:5000 and load the LLM of your choice.

Alternatively, if your local machine can't handle an LLM, rent a GPU somewhere and use that URL/port instead.

Start koboldai-interceptor locally:

```
cd ./koboldai_interceptor
python3 -m venv venv
source venv/bin/activate
pip3 install --upgrade pip
pip3 install -r requirements.txt
spacy download en_core_web_sm
uvicorn app.api:app --port 9000 --reload
```

Start TavernAI from its directory with:

```
node server.js
```

This will start TavernAI on port 8000 on your local machine.

In TavernAI settings, set the KoboldAI API url to http://127.0.0.1:5000/api (or your rented GPU instance URL) and start chatting!
