FROM python:3.10

RUN pip3 install poetry==1.4.1

WORKDIR /app
COPY poetry.lock pyproject.toml /app
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi
RUN poetry run spacy download en_core_web_sm

COPY . /app
RUN mkdir /app/data

# TODO figure out how to pull transformers models into a layer instead of fetching them
# on first run

ENV UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=9000 \
    UVICORN_LOG_LEVEL=debug \
    WEB_CONCURRENCY=2 \
    AI_DATA_DIR=/app/data

EXPOSE 9000

CMD ["uvicorn", "app.api:app"]
