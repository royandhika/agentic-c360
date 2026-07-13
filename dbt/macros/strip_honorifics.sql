{% macro strip_honorifics(name_col) %}
    if(
        nullif(trim({{ name_col }}), '') IS NULL OR {{ name_col }} IS NULL,
        NULL,
        trim(
            arrayStringConcat(
                arrayMap(
                    x -> concat(upper(substring(x, 1, 1)), lower(substring(x, 2))),
                    splitByChar(' ',
                        replaceRegexpOne(
                            replaceRegexpOne(
                                lower(trim({{ name_col }})),
                                '^(bpk\.|ibu|sdr\.|h\.|drs\.|dr\.|drg\.|ir\.|tgk\.|dt\.|r\.|r\.a\.)[\s]+',
                                ''
                            ),
                            ',\s*(s\.(kom|ip|farm|ked|sos|psi|h|e)\.|m\.(kom|m|t)\.)[\s]*$',
                            ''
                        )
                    )
                ),
                ' '
            )
        )
    )::Nullable(String)
{% endmacro %}
