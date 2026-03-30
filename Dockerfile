FROM python:3.12-slim

RUN pip install uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY src/ ./src/
COPY .env.example .env.example

EXPOSE 8000

CMD ["uv", "run", "granian", "--interface", "asgi", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
