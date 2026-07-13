import json
import os

import dagster as dg
from dagster_dbt import (
    DagsterDbtTranslator,
    DbtCliResource,
    DbtProject,
    dbt_assets,
)

daily_partitions = dg.DailyPartitionsDefinition(start_date="2026-01-01")

project_dir = os.getenv("DBT_PROJECT_DIR", "/opt/dagster/dbt")
profiles_dir = os.getenv("DBT_PROFILES_DIR", "/opt/dagster/ops")

dbt_project = DbtProject(project_dir=project_dir, profiles_dir=profiles_dir)
dbt_project.prepare_if_dev()

SILVER_TO_BRONZE = {
    "silver_customers": [["bronze", "customers"]],
    "silver_hotel_bookings": [["bronze", "hotel_bookings"]],
    "silver_flight_bookings": [["bronze", "flights"]],
    "silver_experience_bookings": [["bronze", "experiences"]],
    "silver_tickets": [["bronze", "tickets"]],
}


class WanderFuelDbtTranslator(DagsterDbtTranslator):
    def get_asset_spec(self, manifest, unique_id, project):
        base_spec = super().get_asset_spec(manifest, unique_id, project)
        dbt_props = self.get_resource_props(manifest, unique_id)
        model_name = dbt_props.get("name", "")
        return base_spec.replace_attributes(
            group_name="silver",
            owners=["team:data-engineering"],
            tags={"layer": "silver", "pii": "true", "domain": "travel"},
            kinds=["dbt", "clickhouse", "table"],
            deps=[dg.AssetKey(k) for k in SILVER_TO_BRONZE.get(model_name, [])],
        )


@dbt_assets(
    manifest=dbt_project.manifest_path,
    partitions_def=daily_partitions,
    dagster_dbt_translator=WanderFuelDbtTranslator(),
)
def wanderfuel_dbt_assets(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    time_window = context.partition_time_window
    dbt_vars = {
        "min_date": time_window.start.strftime("%Y-%m-%d"),
        "max_date": time_window.end.strftime("%Y-%m-%d"),
    }
    yield from dbt.cli(["build", "--vars", json.dumps(dbt_vars)], context=context).stream()
