# Phase 2a — Bronze Landing Pattern

## Architecture

```
definitions.py          load_assets_from_package_module + load_asset_checks_from_package_module
resources.py            ConfigurableResource classes (EnvVar for config)
assets/
  __init__.py           (empty — enables package module scanning)
  landing.py            1 source → 1 module, asset + checks colocated
```

## Resource classes (`resources.py`)

```python
from dagster import ConfigurableResource, EnvVar

class PostgresResource(ConfigurableResource):
    host: str = EnvVar("POSTGRES_APP_HOST")
    port: int = EnvVar.int("POSTGRES_APP_PORT")
    user: str = EnvVar("POSTGRES_APP_USER")
    password: str = EnvVar("POSTGRES_APP_PASS")
    dbname: str = EnvVar("POSTGRES_APP_DB")

    def get_connection(self):
        return psycopg2.connect(host=self.host, port=self.port, ...)
```

- **Always use `EnvVar`** for credentials/config — no `os.getenv()` in resources or definitions
- **`EnvVar.int()`** for integer env vars like port
- Register resources bare in definitions: `PostgresResource()`

## Asset module (`assets/landing.py`)

### Module-level shared state
- `daily_partitions = dg.DailyPartitionsDefinition(start_date="...")` — shared across all assets
- `_DTYPE_MAP` + `_map_dtype(dtype)` — maps pandas dtypes to Dagster-friendly column type names (object→string, int64→integer, datetime64[ns]→datetime, etc.)
- `_build_path(bucket, batch_date)` — shared path builder, avoids duplication between asset and checks
- `_read_parquet(minio, path)` — shared parquet reader for checks

### Asset decorator signature
```python
@dg.asset(
    key_prefix=["bronze"],
    description="English description of what this asset is and contains",
    group_name="landing",
    owners=["team:data-engineering"],
    tags={"layer": "bronze", "pii": "true", "domain": "travel"},
    kinds=["parquet", "s3"],
    partitions_def=daily_partitions,
)
```

- **`group_name="landing"`** — all bronze assets share this group
- **`kinds=["parquet", "s3"]`** — conveys destination type and storage
- **`pii` tag** — `"true"` for identity data, `"false"` otherwise (used by downstream masking/anonymization)
- **No `metadata=` on decorator** — column schema goes in `MaterializeResult`, not definition metadata

### Asset function signature
```python
def asset_name(
    context: dg.AssetExecutionContext,
    postgres: PostgresResource,      # type-annotated resource injects automatically
    minio: MinIOResource,
):
```

- Resources are injected by **type annotation**, not string keys
- `context.partition_key` gives `YYYY-MM-DD` batch date

### Materialization metadata (returned, not decorated)
```python
return dg.MaterializeResult(metadata={
    "dagster/column_schema": dg.MetadataValue.table_schema(column_schema),
    "dagster/row_count": dg.MetadataValue.int(rows),
    "path": dg.MetadataValue.text(path),
    "batch_date": dg.MetadataValue.text(batch_date),
})
```

- **`dagster/column_schema`** — built from `df.dtypes` at runtime (data-driven, not manual lists)
- **`dagster/row_count`** — standard Dagster metadata key
- Column types are mapped via `_map_dtype()` to get proper UI icons

### Parquet write path convention
```
s3://{bucket}/app_oltp/customers/year={YYYY}/month={MM}/day={DD}/customers_{YYYYMMDD}.parquet
```

Hive-style partitioning: `source={source}` prefix, then `year=/month=/day=` partition columns.

## Asset checks (colocated with the asset)

```python
@dg.asset_check(
    asset=customers,
    description="What this check validates",
)
def check_name(context: dg.AssetCheckExecutionContext, minio: MinIOResource):
    batch_date = context.partition_key
    path = _build_path(minio.bucket, batch_date)
    df = _read_parquet(minio, path)

    passed = ...
    return dg.AssetCheckResult(passed=passed, metadata={...})
```

- **Colocated** in the same module as the asset they target
- **Reuse `_build_path` and `_read_parquet`** — read the parquet back from MinIO
- Use `context.partition_key` to know which partition to validate
- Use `AssetCheckExecutionContext` (not `AssetExecutionContext`)

### Standard bronze checks (per asset)
| Check | Validates |
|-------|-----------|
| `{asset}_not_empty` | Row count > 0 |
| `{asset}_no_null_pks` | Primary key column(s) have no nulls |
| `{asset}_unique_pks` | Primary key column(s) have no duplicates |

## Definitions (`definitions.py`)

```python
from . import assets
from .resources import MinIOResource, PostgresResource

landing_assets = dg.load_assets_from_package_module(assets)
landing_checks = dg.load_asset_checks_from_package_module(assets)

defs = dg.Definitions(
    assets=landing_assets,
    asset_checks=landing_checks,
    resources={
        "postgres": PostgresResource(),
        "minio": MinIOResource(),
    },
)
```

- **`load_assets_from_package_module`** — scans `assets/` package for `@dg.asset`-decorated functions
- **`load_asset_checks_from_package_module`** — scans `assets/` package for `@dg.asset_check`-decorated functions
- Resources instantiated **bare** (no args) — all config via `EnvVar`

## Adding a new bronze asset (checklist)

1. Add `_build_path` for the new source/table (or parameterize the existing one)
2. Write `@dg.asset` following the signature conventions above
3. Write 3 `@dg.asset_check` functions targeting the new asset
4. Run `dg list defs` to verify registration
