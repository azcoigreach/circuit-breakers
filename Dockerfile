FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --upgrade pip \
    && pip install -e .[dev]

COPY app ./app

CMD ["uvicorn", "app.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
