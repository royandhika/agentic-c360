{{ config(materialized='incremental', unique_key='booking_ref') }}

with source as (
    select
        booking_ref::String as booking_ref,
        email::String as email,
        experience_name::String as experience_name,
        city::String as city,
        category::String as category,
        activity_date::String as activity_date,
        participants::Int64 as participants,
        amount_idr::Int64 as amount_idr,
        payment_method::String as payment_method,
        booking_status::String as booking_status,
        booking_ts::String as booking_ts
    from {{ bronze_s3_path('vendor_api', 'experiences', var('min_date'), var('max_date')) }}
),

cleansed as (
    select
        booking_ref,
        {{ normalize_email('email') }} as email,
        trim(
            arrayStringConcat(
                arrayMap(
                    x -> concat(upper(substring(x, 1, 1)), lower(substring(x, 2))),
                    splitByChar(' ', lower(trim(experience_name)))
                ),
                ' '
            )
        ) as experience_name,
        trim(
            arrayStringConcat(
                arrayMap(
                    x -> concat(upper(substring(x, 1, 1)), lower(substring(x, 2))),
                    splitByChar(' ', lower(trim(city)))
                ),
                ' '
            )
        ) as city,
        lower(trim(category)) as category,
        toDate(parseDateTimeBestEffortOrNull(activity_date)) as activity_date,
        coalesce(nullif(participants, 0), 1) as participants,
        {{ normalize_amount_idr('amount_idr') }} as amount_idr,
        multiIf(
            lower(trim(payment_method)) = 'bank transfer bca', 'Bank Transfer (BCA)',
            lower(trim(payment_method)) = 'bank transfer mandiri', 'Bank Transfer (Mandiri)',
            lower(trim(payment_method)) = 'bank transfer bri', 'Bank Transfer (BRI)',
            lower(trim(payment_method)) = 'bank transfer bni', 'Bank Transfer (BNI)',
            trim(
                arrayStringConcat(
                    arrayMap(
                        x -> concat(upper(substring(x, 1, 1)), lower(substring(x, 2))),
                        splitByChar(' ', lower(trim(payment_method)))
                    ),
                    ' '
                )
            )
        ) as payment_method,
        multiIf(
            lower(trim(booking_status)) = 'batal', 'cancelled',
            lower(trim(booking_status)) = 'selesai', 'completed',
            lower(trim(booking_status)) = 'tidak_hadir', 'no_show',
            lower(trim(booking_status))
        ) as booking_status,
        formatDateTime(parseDateTimeBestEffortOrNull(booking_ts), '%Y-%m-%d %H:%M:%S') as booking_ts
    from source
),

deduped as (
    select *,
        row_number() over (
            partition by trim(lower(email)),
                trim(lower(experience_name)),
                activity_date,
                amount_idr
            order by booking_ref asc
        ) as rn
    from cleansed
)

select
    booking_ref,
    email,
    experience_name,
    city,
    category,
    activity_date,
    participants,
    amount_idr,
    payment_method,
    booking_status,
    booking_ts
from deduped
where rn = 1
