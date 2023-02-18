# KoboldAI Interceptor

Request/response interception proof-of-concept

Tested with Python 3.11.

---

## Resources
This project has two key dependencies:

| Dependency Name | Documentation                | Description                                                                            |
|-----------------|------------------------------|----------------------------------------------------------------------------------------|
| spaCy           | https://spacy.io             | Industrial-strength Natural Language Processing (NLP) with Python and Cython           |
| FastAPI         | https://fastapi.tiangolo.com | FastAPI framework, high performance, easy to learn, fast to code, ready for production |
---

## Run Locally
To run locally in debug mode run:

```
cd ./koboldai_interceptor
python3 -m venv venv
source venv/bin/activate
pip3 install --upgrade pip
pip3 install -r requirements.txt
uvicorn app.api:app --reload
```
Open your browser to http://localhost:8000/docs to view the OpenAPI UI.

![Open API Image](./images/cookiecutter-docs.png)


For an alternate view of the docs navigate to http://localhost:8000/redoc

---
