import io
import os
from datetime import datetime

import dagster as dg
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import s3fs

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "minio:9000")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "wanderfuel-bronze")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "")


class LandingConfig(dg.Config):
    batch_date: str


def _build_s3() -> s3fs.S3FileSystem:
    return s3fs.S3FileSystem(
        key=MINIO_ACCESS_KEY,
        secret=MINIO_SECRET_KEY,
        client_kwargs={"endpoint_url": f"http://{MINIO_ENDPOINT}"},
    )


def _write_parquet(df: pd.DataFrame, source: str, table: str, batch_date: str) -> tuple[str, int]:
    s3 = _build_s3()
    dt = datetime.strptime(batch_date, "%Y-%m-%d")
    path = (
        f"s3://{MINIO_BUCKET}/{source}/{table}"
        f"/year={dt.year}/month={dt.month:02d}/day={dt.day:02d}"
        f"/{table}_{dt.strftime('%Y%m%d')}.parquet"
    )
    t = pa.Table.from_pandas(df)
    with s3.open(path, "wb") as f:
        pq.write_table(t, f)
    logger = dg.get_dagster_logger()
    logger.info(f"Wrote {len(df)} rows to {path}")
    return path, len(df)


@dg.asset(
    key_prefix=["bronze"],
    description="Land hotel_bookings from app OLTP (Postgres) filtered by batch_date",
)
def hotel_bookings(context: dg.AssetExecutionContext, config: LandingConfig):
    import psycopg2

    batch_date = config.batch_date
    context.log.info(f"Landing hotel_bookings for {batch_date}")

    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_APP_HOST"),
        port=int(os.environ.get("POSTGRES_APP_PORT", 5432)),
        user=os.environ.get("POSTGRES_APP_USER"),
        password=os.environ.get("POSTGRES_APP_PASS"),
        dbname=os.environ.get("POSTGRES_APP_DB"),
    )

    query = "SELECT * FROM hotel_bookings WHERE booking_ts::date = %s"
    df = pd.read_sql_query(query, conn, params=(batch_date,))
    conn.close()

    path, rows = _write_parquet(df, "app_oltp", "hotel_bookings", batch_date)
    return dg.MaterializeResult(
        metadata={
            "rows": dg.MetadataValue.int(rows),
            "path": dg.MetadataValue.text(path),
            "batch_date": dg.MetadataValue.text(batch_date),
        }
    )


@dg.asset(
    key_prefix=["bronze"],
    description="Land customers full snapshot from app OLTP (Postgres)",
)
def customers(context: dg.AssetExecutionContext, config: LandingConfig):
    import psycopg2

    batch_date = config.batch_date
    context.log.info("Landing customers snapshot")

    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_APP_HOST"),
        port=int(os.environ.get("POSTGRES_APP_PORT", 5432)),
        user=os.environ.get("POSTGRES_APP_USER"),
        password=os.environ.get("POSTGRES_APP_PASS"),
        dbname=os.environ.get("POSTGRES_APP_DB"),
    )

    df = pd.read_sql_query("SELECT * FROM customers", conn)
    conn.close()

    path, rows = _write_parquet(df, "app_oltp", "customers", batch_date)
    return dg.MaterializeResult(
        metadata={
            "rows": dg.MetadataValue.int(rows),
            "path": dg.MetadataValue.text(path),
            "batch_date": dg.MetadataValue.text(batch_date),
        }
    )


@dg.asset(
    key_prefix=["bronze"],
    description="Land flight_bookings from vendor API",
)
def flight_bookings(context: dg.AssetExecutionContext, config: LandingConfig):
    import requests

    batch_date = config.batch_date
    context.log.info(f"Landing flight_bookings for {batch_date}")

    vendor_api_url = os.environ.get("VENDOR_API_URL", "http://vendor_api:8000")
    url = f"{vendor_api_url}/flights?since={batch_date}T00:00:00&until={batch_date}T23:59:59"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    df = pd.DataFrame(data)

    path, rows = _write_parquet(df, "vendor_api", "flight_bookings", batch_date)
    return dg.MaterializeResult(
        metadata={
            "rows": dg.MetadataValue.int(rows),
            "path": dg.MetadataValue.text(path),
            "batch_date": dg.MetadataValue.text(batch_date),
        }
    )


@dg.asset(
    key_prefix=["bronze"],
    description="Land experience_bookings from vendor API",
)
def experience_bookings(context: dg.AssetExecutionContext, config: LandingConfig):
    import requests

    batch_date = config.batch_date
    context.log.info(f"Landing experience_bookings for {batch_date}")

    vendor_api_url = os.environ.get("VENDOR_API_URL", "http://vendor_api:8000")
    url = f"{vendor_api_url}/experiences?since={batch_date}T00:00:00&until={batch_date}T23:59:59"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    df = pd.DataFrame(data)

    path, rows = _write_parquet(df, "vendor_api", "experience_bookings", batch_date)
    return dg.MaterializeResult(
        metadata={
            "rows": dg.MetadataValue.int(rows),
            "path": dg.MetadataValue.text(path),
            "batch_date": dg.MetadataValue.text(batch_date),
        }
    )


@dg.asset(
    key_prefix=["bronze"],
    description="Land tickets from CRM SFTP (JSON exports)",
)
def tickets(context: dg.AssetExecutionContext, config: LandingConfig):
    import paramiko

    batch_date = config.batch_date
    context.log.info(f"Landing tickets for {batch_date}")

    host = os.environ.get("CRM_SFTP_HOST")
    port = int(os.environ.get("CRM_SFTP_PORT", 22))
    user = os.environ.get("CRM_SFTP_USER")
    password = os.environ.get("CRM_SFTP_PASS")

    dt = datetime.strptime(batch_date, "%Y-%m-%d")
    remote_path = f"tickets/{dt.year}/{dt.month:02d}/{dt.day:02d}/tickets_{dt.strftime('%Y%m%d')}.json"

    transport = paramiko.Transport((host, port))
    transport.connect(username=user, password=password)
    sftp = paramiko.SFTPClient.from_transport(transport)

    with sftp.open(remote_path, "r") as f:
        content = f.read()
    df = pd.read_json(io.BytesIO(content))

    sftp.close()
    transport.close()

    path, rows = _write_parquet(df, "crm", "tickets", batch_date)
    return dg.MaterializeResult(
        metadata={
            "rows": dg.MetadataValue.int(rows),
            "path": dg.MetadataValue.text(path),
            "batch_date": dg.MetadataValue.text(batch_date),
        }
    )
