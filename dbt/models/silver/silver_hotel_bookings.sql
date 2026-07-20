{{ config(materialized='incremental', unique_key='booking_id') }}

with source as (
    select
        booking_id::String as booking_id,
        customer_id::String as customer_id,
        hotel_name::String as hotel_name,
        hotel_city::String as hotel_city,
        check_in_date::String as check_in_date,
        check_out_date::String as check_out_date,
        room_type::String as room_type,
        guests::Int64 as guests,
        amount_idr::Int64 as amount_idr,
        payment_method::String as payment_method,
        booking_status::String as booking_status,
        booking_ts::String as booking_ts
    from {{ bronze_table('hotel_bookings', var('min_date'), var('max_date')) }}
),

cleansed as (
    select
        booking_id,
        customer_id,
        trim(
            arrayStringConcat(
                arrayMap(
                    x -> concat(upper(substring(x, 1, 1)), lower(substring(x, 2))),
                    splitByChar(' ', lower(trim(hotel_name)))
                ),
                ' '
            )
        ) as hotel_name,
        trim(
            arrayStringConcat(
                arrayMap(
                    x -> concat(upper(substring(x, 1, 1)), lower(substring(x, 2))),
                    splitByChar(' ', lower(trim(hotel_city)))
                ),
                ' '
            )
        ) as hotel_city,
        toDate(parseDateTimeBestEffortOrNull(check_in_date)) as check_in_date,
        toDate(parseDateTimeBestEffortOrNull(check_out_date)) as check_out_date,
        trim(
            arrayStringConcat(
                arrayMap(
                    x -> concat(upper(substring(x, 1, 1)), lower(substring(x, 2))),
                    splitByChar(' ', lower(trim(room_type)))
                ),
                ' '
            )
        ) as room_type,
        coalesce(guests, 1) as guests,
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
        parseDateTimeBestEffortOrNull(booking_ts) as booking_ts
    from source
),

deduped as (
    select *,
        row_number() over (
            partition by customer_id,
                trim(lower(hotel_name)),
                check_in_date,
                amount_idr
            order by booking_id asc
        ) as rn
    from cleansed
)

select
    booking_id,
    customer_id,
    hotel_name,
    hotel_city,
    check_in_date,
    check_out_date,
    room_type,
    guests,
    amount_idr,
    payment_method,
    booking_status,
    booking_ts
from deduped
where rn = 1
