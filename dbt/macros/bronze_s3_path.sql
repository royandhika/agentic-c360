{% macro bronze_s3_path(source, table, min_date, max_date) %}
    {% set min_date = min_date or '2026-01-01' %}
    {% set max_date = max_date or '2026-01-01' %}
    {% if min_date == max_date %}
        {% set year = min_date[:4] %}
        {% set month = min_date[5:7] %}
        {% set day = min_date[8:10] %}
        {% set yyyymmdd = year ~ month ~ day %}
        (select * from s3('http://minio:9000/wanderfuel-bronze/{{ source }}/{{ table }}/year={{ year }}/month={{ month }}/day={{ day }}/{{ table }}_{{ yyyymmdd }}.parquet', '{{ env_var("MINIO_ACCESS_KEY") }}', '{{ env_var("MINIO_SECRET_KEY") }}', 'Parquet') SETTINGS input_format_parquet_allow_missing_columns=1)
    {% else %}
        (select * from s3('http://minio:9000/wanderfuel-bronze/{{ source }}/{{ table }}/year=*/month=*/day=*/{{ table }}_*.parquet', '{{ env_var("MINIO_ACCESS_KEY") }}', '{{ env_var("MINIO_SECRET_KEY") }}', 'Parquet') where _file between '{{ table }}_{{ min_date | replace("-", "") }}.parquet' and '{{ table }}_{{ max_date | replace("-", "") }}.parquet' SETTINGS input_format_parquet_allow_missing_columns=1)
    {% endif %}
{% endmacro %}
