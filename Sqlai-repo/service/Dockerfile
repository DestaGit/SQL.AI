FROM python:3.12.7-slim

RUN useradd --create-home --uid 10001 sqlai
WORKDIR /app
COPY pyproject.toml ./
COPY sqlai ./sqlai
COPY policy ./policy
RUN pip install --no-cache-dir . && python -m sqlai.demo_data /app/data/warehouse.duckdb && chown -R sqlai /app/data

USER sqlai
ENV SQLAI_ENV=local SQLAI_DATA_DIR=/app/data
EXPOSE 8000
# Local demo image. Outside local, set SQLAI_ENV, SQLAI_AUDIT_KEY (32+ chars) and an OIDC identity provider.
CMD ["python", "-c", "import uvicorn; from sqlai.api import create_app; uvicorn.run(create_app(), host='0.0.0.0', port=8000)"]
