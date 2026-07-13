{% macro normalize_amount_idr(amount_col) %}
    multiIf(
        {{ amount_col }} IS NULL OR nullif(trim(toString({{ amount_col }})), '') IS NULL, NULL,
        toInt64OrZero(
            replaceRegexpAll(
                replaceRegexpAll(
                    trim(
                        if(
                            startsWith(trim(toString({{ amount_col }})), 'Rp'),
                            substring(trim(toString({{ amount_col }})), 3),
                            toString({{ amount_col }})
                        )
                    ),
                    '\.',
                    ''
                ),
                ',.*$',
                ''
            )
        ) = 0, NULL,
        round(
            toInt64OrZero(
                replaceRegexpAll(
                    replaceRegexpAll(
                        trim(
                            if(
                                startsWith(trim(toString({{ amount_col }})), 'Rp'),
                                substring(trim(toString({{ amount_col }})), 3),
                                toString({{ amount_col }})
                            )
                        ),
                        '\.',
                        ''
                    ),
                    ',.*$',
                    ''
                )
            ) / 100,
            0
        ) * 100
    )::Nullable(Int64)
{% endmacro %}
