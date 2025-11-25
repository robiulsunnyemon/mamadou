# ---- Base image ----
FROM python:3.11-slim

# ---- Set working directory ----
WORKDIR /app

# ---- Install Poetry ----
RUN pip install --no-cache-dir poetry

# ---- Copy project files ----
COPY pyproject.toml poetry.lock* ./

# ---- Install dependencies without installing the root package ----
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# ---- Copy source code ----
COPY ./src ./src

# ---- Expose port ----
EXPOSE 8000

# ---- Run FastAPI with Uvicorn ----
CMD ["uvicorn", "src.mamadou.main:app", "--host", "0.0.0.0", "--port", "8000"]