# ---- Base image ----
FROM python:3.11-slim

# ---- Working directory ----
WORKDIR /app

# ---- সব ফাইল কপি করুন ----
COPY . .

# ---- Poetry ইন্সটল করুন ----
RUN pip install --no-cache-dir poetry

# ---- dependencies ইন্সটল করুন (--no-root বাদ দিন) ----
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# ---- PYTHONPATH সেট করুন ----
ENV PYTHONPATH=/app/src:$PYTHONPATH

# ---- Port ----
EXPOSE 8000

# ---- Run the app ----
CMD ["uvicorn", "api_naturalize.main:app", "--host", "0.0.0.0", "--port", "8000"]