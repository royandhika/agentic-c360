import dagster as dg
from dagster_dbt import DbtCliResource

from . import assets
from .dbt_assets import dbt_project, wanderfuel_dbt_assets
from .resources import (
    ClickHouseResource,
    PostgresResource,
    SFTPSourceResource,
    VendorApiResource,
)

landing_assets = dg.load_assets_from_package_module(assets)
landing_checks = dg.load_asset_checks_from_package_module(assets)

defs = dg.Definitions(
    assets=[*landing_assets, wanderfuel_dbt_assets],
    asset_checks=landing_checks,
    resources={
        "postgres": PostgresResource(),
        "vendor_api": VendorApiResource(),
        "crm_sftp": SFTPSourceResource(),
        "clickhouse": ClickHouseResource(),
        "dbt": DbtCliResource(project_dir=dbt_project.project_dir),
    },
)
