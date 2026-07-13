{% macro normalize_phone(phone_col) %}
    multiIf(
        toString({{ phone_col }}) IN ('TIDAK ADA', 'tidak diketahui', '000-000-0000', '', '0') OR {{ phone_col }} IS NULL, NULL,
        startsWith(arrayStringConcat(extractAll(toString({{ phone_col }}), '\d'), ''), '+62'), concat('+', arrayStringConcat(extractAll(toString({{ phone_col }}), '\d'), '')),
        startsWith(arrayStringConcat(extractAll(toString({{ phone_col }}), '\d'), ''), '62'), concat('+', arrayStringConcat(extractAll(toString({{ phone_col }}), '\d'), '')),
        startsWith(arrayStringConcat(extractAll(toString({{ phone_col }}), '\d'), ''), '0'), concat('+62', substring(arrayStringConcat(extractAll(toString({{ phone_col }}), '\d'), ''), 2)),
        length(arrayStringConcat(extractAll(toString({{ phone_col }}), '\d'), '')) >= 10, concat('+62', arrayStringConcat(extractAll(toString({{ phone_col }}), '\d'), '')),
        NULL
    )::Nullable(String)
{% endmacro %}
