FROM python:3.13 AS build

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.5

RUN apt-get update && apt-get install -y curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry \
    && apt-get remove -y curl \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock /app/
RUN poetry config virtualenvs.create true && poetry config virtualenvs.in-project true \
    && poetry install --no-interaction

COPY . .

ENV PYTHONPATH=/app
CMD ["poetry", "run", "python3", "-m", "traffic_management.app"]
