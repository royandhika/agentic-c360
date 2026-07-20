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
    "silver_customers": [["bronze_customers"]],
    "silver_hotel_bookings": [["bronze_hotel_bookings"]],
    "silver_flight_bookings": [["bronze_flights"]],
    "silver_experience_bookings": [["bronze_experiences"]],
    "silver_tickets": [["bronze_tickets"]],
}

GOLD_TO_SILVER = {
    "dim_customer": [
        ["silver_customers"],
        ["silver_flight_bookings"],
        ["silver_experience_bookings"],
        ["silver_tickets"],
    ],
    "fact_bookings": [
        ["silver_hotel_bookings"],
        ["silver_flight_bookings"],
        ["silver_experience_bookings"],
        ["dim_customer"],
    ],
    "mart_customer_clv": [
        ["fact_bookings"],
        ["dim_customer"],
        ["silver_tickets"],
    ],
    "mart_route_monthly": [
        ["fact_bookings"],
    ],
}


class WanderFuelDbtTranslator(DagsterDbtTranslator):
    def get_asset_spec(self, manifest, unique_id, project):
        base_spec = super().get_asset_spec(manifest, unique_id, project)
        dbt_props = self.get_resource_props(manifest, unique_id)
        model_name = dbt_props.get("name", "")
        model_path = dbt_props.get("path", "")
        if model_path.startswith("gold/"):
            layer = "gold"
            deps_map = GOLD_TO_SILVER
            tags = {"layer": "gold", "pii": "true", "domain": "travel"}
        else:
            layer = "silver"
            deps_map = SILVER_TO_BRONZE
            tags = {"layer": "silver", "pii": "true", "domain": "travel"}
        return base_spec.replace_attributes(
            group_name=layer,
            owners=["team:data-engineering"],
            tags=tags,
            kinds=["dbt", "clickhouse", "table"],
            deps=[dg.AssetKey(k) for k in deps_map.get(model_name, [])],
        )


class WanderFuelDbtConfig(dg.Config):
    full_refresh: bool = False


@dbt_assets(
    manifest=dbt_project.manifest_path,
    partitions_def=daily_partitions,
    dagster_dbt_translator=WanderFuelDbtTranslator(),
    backfill_policy=dg.BackfillPolicy.single_run(),
)
def wanderfuel_dbt_assets(context: dg.AssetExecutionContext, config: WanderFuelDbtConfig, dbt: DbtCliResource):
    # single_run policy: context.partition_keys is the list of partitions
    # covered by this run. Build a single dbt invocation whose
    # `min_date..max_date` covers the half-open union of all partition
    # windows. The bronze_table macro filters `ingest_date >= min AND < max`,
    # so one dbt run merges all partitions in the range into silver/gold.
    keys = list(context.partition_keys)
    if not keys:
        # Defensive: shouldn't happen for a partitioned asset.
        keys = [context.partition_key]

    if config.full_refresh:
        # Half-open [absolute_first_partition_start, last_partition_end)
        # covers every landed day up to and including the requested range.
        min_date = daily_partitions.get_first_partition_key()
    else:
        min_date = keys[0]

    last_key = keys[-1]
    last_end = daily_partitions.end_time_for_partition_key(last_key)
    max_date = last_end.strftime("%Y-%m-%d")

    dbt_vars = {"min_date": min_date, "max_date": max_date}
    dbt_vars_json = json.dumps(dbt_vars)
    run_args = ["run", "--vars", dbt_vars_json]
    if config.full_refresh:
        run_args.append("--full-refresh")
    yield from dbt.cli(run_args, context=context).stream()
    yield from dbt.cli(["test", "--vars", dbt_vars_json], context=context, raise_on_error=False).stream()
