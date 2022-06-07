FROM python:3.10-slim

ENV POETRY_VERSION 1.1.13

WORKDIR /app

RUN apt-get update && apt-get -y install curl wget git wait-for-it jq && apt-get clean

RUN wget https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py &&  \
    python get-poetry.py --version $POETRY_VERSION && \
    rm get-poetry.py

ENV PATH="${PATH}:/root/.poetry/bin"
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-root

COPY . /app
RUN poetry install --no-interaction

EXPOSE 8000

CMD ["/app/bin/docker-entrypoint.sh"]
