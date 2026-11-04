FROM python:3.12-slim
WORKDIR /app
COPY deploy/requirements.txt ./
RUN pip install --no-cache-dir --require-hashes -r requirements.txt
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir --no-deps .
COPY knowledge ./knowledge
COPY config ./config
ENV HF_HUB_OFFLINE=1 PYTHONUNBUFFERED=1
