{#
  bronze_table(table, min_date, max_date)
  Returns a subquery over the named ClickHouse bronze landing table,
  filtered to the half-open ingest_date range [min_date, max_date).

  Convention: min_date and max_date come from
  dagster_pipeline/dagster_pipeline/dbt_assets.py as partition_time_window
  bounds (start inclusive, end exclusive). On a single-day partition run
  min_date = "2026-07-10" and max_date = "2026-07-11". The strict
  less-than on max_date preserves that half-open semantics, so silver
  models read exactly one ingest_date per partition.
#}
{% macro bronze_table(table, min_date, max_date) %}
    {% set min_date = min_date or '2026-01-01' %}
    {% set max_date = max_date or '2026-01-02' %}
    (select * from wanderfuel.bronze_{{ table }}
     where ingest_date >= toDate('{{ min_date }}')
       and ingest_date <  toDate('{{ max_date }}'))
{% endmacro %}