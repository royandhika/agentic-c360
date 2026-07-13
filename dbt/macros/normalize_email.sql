{% macro normalize_email(email_col) %}
    if(
        nullif(trim(toString({{ email_col }})), '') IS NULL OR {{ email_col }} IS NULL,
        NULL,
        replaceRegexpOne(
            replaceRegexpOne(
                replaceRegexpOne(
                    replaceRegexpOne(
                        trim(lower(toString({{ email_col }}))),
                        '\+[^@]*@',
                        '@'
                    ),
                    '@gnail\.',
                    '@gmail.'
                ),
                '@gmaill\.',
                '@gmail.'
            ),
            '@yaho\.',
            '@yahoo.'
        )
    )::Nullable(String)
{% endmacro %}
