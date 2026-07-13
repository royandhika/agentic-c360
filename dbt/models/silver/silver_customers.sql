{{ config(materialized='incremental', unique_key='customer_id') }}

with source as (
    select
        customer_id::String as customer_id,
        email::String as email,
        phone::String as phone,
        full_name::String as full_name,
        address::String as address,
        city::String as city,
        province::String as province,
        postal_code::String as postal_code,
        loyalty_tier::Nullable(String) as loyalty_tier,
        preferred_airline::Nullable(String) as preferred_airline,
        created_at::String as created_at,
        updated_at::String as updated_at
    from {{ bronze_s3_path('app_oltp', 'customers', var('min_date'), var('max_date')) }}
),

cleansed as (
    select
        customer_id,
        {{ normalize_email('email') }} as email,
        {{ normalize_phone('phone') }} as phone,
        {{ strip_honorifics('full_name') }} as full_name,
        trim(address) as address,
        trim(
            arrayStringConcat(
                arrayMap(
                    x -> concat(upper(substring(x, 1, 1)), lower(substring(x, 2))),
                    splitByChar(' ', lower(trim(city)))
                ),
                ' '
            )
        ) as city,
        trim(
            arrayStringConcat(
                arrayMap(
                    x -> concat(upper(substring(x, 1, 1)), lower(substring(x, 2))),
                    splitByChar(' ', lower(trim(province)))
                ),
                ' '
            )
        ) as province,
        if(
            length(trim(postal_code)) > 5,
            substring(trim(postal_code), 1, 5),
            trim(postal_code)
        ) as postal_code,
        coalesce(nullif(lower(trim(loyalty_tier)), ''), 'basic') as loyalty_tier,
        nullif(trim(preferred_airline), '') as preferred_airline,
        formatDateTime(parseDateTimeBestEffortOrNull(created_at), '%Y-%m-%d %H:%M:%S') as created_at,
        formatDateTime(parseDateTimeBestEffortOrNull(updated_at), '%Y-%m-%d %H:%M:%S') as updated_at
    from source
),

deduped as (
    select *,
        row_number() over (
            partition by customer_id
            order by
                coalesce(updated_at, created_at) desc
        ) as rn
    from cleansed
)

select
    customer_id,
    email,
    phone,
    full_name,
    address,
    city,
    province,
    postal_code,
    loyalty_tier,
    preferred_airline,
    created_at,
    updated_at
from deduped
where rn = 1
