# Databank loaders: one image, one container per run and per source.
# Build (from the repository root):  docker build -f ingestion/Dockerfile -t databank-loader:1.0.0 .
# Run (the key is passed at run time, never stored in the image):
#   docker run --rm -e SNOWFLAKE_ACCOUNT -e SNOWFLAKE_USER -e SNOWFLAKE_PRIVATE_KEY \
#     databank-loader:1.0.0 python -m ingestion.d_ecb_api.ingest_ecb_fx

# 1. Pinned base image: the same Python on every machine
FROM python:3.11.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 2. Dependencies first (pinned with ==), so this layer is cached when only the code changes
COPY ingestion/requirements.txt ingestion/requirements.txt
RUN pip install -r ingestion/requirements.txt

# 3. Then the code
COPY ingestion/ ingestion/

# 4. Never run as root
RUN useradd --create-home --uid 10001 loader
USER loader

# Default job: source D (ECB API, incremental). Any loader can be chosen at run time.
CMD ["python", "-m", "ingestion.d_ecb_api.ingest_ecb_fx"]
