FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/packages:/app/services/auth-service/src:/app/services/entitlement-service/src:/app/services/ingestion-service/src:/app/services/observability-service/src:/app/services/policy-service/src:/app/services/retrieval-service/src:/app/services/reranker-service/src:/app/services/llm-gateway/src:/app/services/verification-service/src:/app/services/context-service/src:/app/services/assistant-api/src:/app/services/eval-service/src
ENV PORT=8000

WORKDIR /app

RUN pip install --no-cache-dir \
    "fastapi>=0.115.0" \
    "httpx>=0.27.0" \
    "pydantic>=2.8.0" \
    "uvicorn[standard]>=0.30.0"

COPY packages ./packages
COPY services ./services
COPY configs ./configs
COPY data ./data

CMD ["sh", "-c", "python -m uvicorn ${AEGIS_SERVICE_APP} --host 0.0.0.0 --port ${PORT}"]
