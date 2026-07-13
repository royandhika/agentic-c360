from datetime import datetime

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from dagster_pipeline.resources import MinIOResource

_DTYPE_MAP = {
    "object": "string",
    "str": "string",
    "int64": "integer",
    "Int64": "integer",
    "float64": "float",
    "Float64": "float",
    "datetime64[ns]": "datetime",
    "datetime64[us]": "datetime",
    "datetime64[ns, UTC]": "datetime",
}


def _map_dtype(dtype) -> str:
    return _DTYPE_MAP.get(str(dtype), str(dtype))


def _build_path(bucket: str, source: str, table: str, batch_date: str) -> str:
    dt = datetime.strptime(batch_date, "%Y-%m-%d")
    return (
        f"s3://{bucket}/{source}/{table}"
        f"/year={dt.year}/month={dt.month:02d}/day={dt.day:02d}"
        f"/{table}_{dt.strftime('%Y%m%d')}.parquet"
    )


def _read_parquet(minio: MinIOResource, path: str) -> pd.DataFrame:
    s3 = minio.get_s3()
    with s3.open(path, "rb") as f:
        table = pq.read_table(f)
    return table.to_pandas()


def _write_parquet(minio: MinIOResource, path: str, df: pd.DataFrame) -> None:
    s3 = minio.get_s3()
    table = pa.Table.from_pandas(df)
    with s3.open(path, "wb") as f:
        pq.write_table(table, f)
