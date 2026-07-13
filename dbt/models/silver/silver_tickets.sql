{{ config(materialized='incremental', unique_key='ticket_id') }}

with source as (
    select
        ticket_id::String as ticket_id,
        customer_email::String as customer_email,
        customer_phone::String as customer_phone,
        customer_name::String as customer_name,
        subject::String as subject,
        body::String as body,
        status::String as status,
        priority::String as priority,
        channel::String as channel,
        created_at::String as created_at,
        resolved_at::Nullable(String) as resolved_at,
        category::String as category,
        agent_name::String as agent_name
    from {{ bronze_s3_path('crm', 'tickets', var('min_date'), var('max_date')) }}
),

cleansed as (
    select
        ticket_id,
        {{ normalize_email('customer_email') }} as customer_email,
        {{ normalize_phone('customer_phone') }} as customer_phone,
        {{ strip_honorifics('customer_name') }} as customer_name,
        trim(subject) as subject,
        trim(replaceRegexpAll(body, '[ÂâÃãÄäÅå]', '')) as body,
        lower(trim(status)) as status,
        lower(trim(priority)) as priority,
        lower(trim(channel)) as channel,
        formatDateTime(parseDateTimeBestEffortOrNull(created_at), '%Y-%m-%d %H:%M:%S') as created_at,
        formatDateTime(parseDateTimeBestEffortOrNull(resolved_at), '%Y-%m-%d %H:%M:%S') as resolved_at,
        lower(trim(category)) as category,
        trim(
            arrayStringConcat(
                arrayMap(
                    x -> concat(upper(substring(x, 1, 1)), lower(substring(x, 2))),
                    splitByChar(' ', lower(trim(agent_name)))
                ),
                ' '
            )
        ) as agent_name
    from source
),

deduped as (
    select *,
        row_number() over (
            partition by ticket_id
            order by created_at desc
        ) as rn
    from cleansed
)

select
    ticket_id,
    customer_email,
    customer_phone,
    customer_name,
    subject,
    body,
    status,
    priority,
    channel,
    created_at,
    resolved_at,
    category,
    agent_name
from deduped
where rn = 1
