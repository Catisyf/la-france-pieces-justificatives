# ---- Base Python image ----
FROM python:3.12-slim

# ---- System dependencies ----
RUN apt-get update && apt-get install -y curl build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# ---- Install Poetry v2.1.3 ----
ENV POETRY_VERSION=2.1.3
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    /root/.local/bin/poetry self update $POETRY_VERSION && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# ---- Set workdir ----
WORKDIR /app

# ---- Copy dependency files first for better caching ----
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \ 
    && poetry install --no-root --only main --no-cache

# ---- Copy rest of the project ----
COPY . .

# ---- Expose Streamlit port ----
EXPOSE 8080

# ---- Start the app ----
CMD ["./entrypoint.sh"]