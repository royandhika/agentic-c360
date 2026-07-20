{{ config(materialized='incremental', unique_key='booking_ref') }}

with source as (
    select
        booking_ref::String as booking_ref,
        email::String as email,
        airline::String as airline,
        flight_number::String as flight_number,
        origin::String as origin,
        destination::String as destination,
        departure_ts::String as departure_ts,
        arrival_ts::String as arrival_ts,
        passenger_name::String as passenger_name,
        seat_class::String as seat_class,
        amount_idr::Int64 as amount_idr,
        payment_method::String as payment_method,
        booking_status::String as booking_status,
        booking_ts::String as booking_ts
    from {{ bronze_table('flights', var('min_date'), var('max_date')) }}
),

cleansed as (
    select
        booking_ref,
        {{ normalize_email('email') }} as email,
        trim(
            arrayStringConcat(
                arrayMap(
                    x -> concat(upper(substring(x, 1, 1)), lower(substring(x, 2))),
                    splitByChar(' ', lower(trim(airline)))
                ),
                ' '
            )
        ) as airline,
        upper(trim(flight_number)) as flight_number,
        upper(trim(origin)) as origin,
        upper(trim(destination)) as destination,
        parseDateTimeBestEffortOrNull(departure_ts) as departure_ts,
        parseDateTimeBestEffortOrNull(arrival_ts) as arrival_ts,
        {{ strip_honorifics('passenger_name') }} as passenger_name,
        lower(trim(seat_class)) as seat_class,
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
            partition by trim(lower(email)),
                upper(trim(flight_number)),
                departure_ts,
                amount_idr
            order by booking_ref asc
        ) as rn
    from cleansed
)

select
    booking_ref,
    email,
    airline,
    flight_number,
    origin,
    destination,
    departure_ts,
    arrival_ts,
    passenger_name,
    seat_class,
    amount_idr,
    payment_method,
    booking_status,
    booking_ts
from deduped
where rn = 1
