FROM python:3.12-slim
WORKDIR /opt/dagster
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir dagster dagster-webserver dagster-postgres
RUN pip install --no-cache-dir pandas pyarrow boto3 s3fs clickhouse-connect
RUN pip install --no-cache-dir psycopg2-binary requests paramiko python-dotenv pytest
RUN pip install --no-cache-dir dagster-dbt dbt-core dbt-clickhouse
RUN mkdir -p /opt/dagster/dagster_home
ENV DAGSTER_HOME=/opt/dagster/dagster_home
