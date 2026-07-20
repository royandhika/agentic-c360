{{ config(materialized='incremental', unique_key='booking_id') }}

with hotel as (
    select
        booking_id,
        'app:' || customer_id as _lookup,
        'app_oltp' as source,
        'hotel' as booking_type,
        hotel_name as provider,
        hotel_city as city,
        cast(null as Nullable(String)) as origin,
        cast(null as Nullable(String)) as destination,
        amount_idr,
        payment_method,
        booking_ts,
        booking_status as status,
        check_in_date,
        check_out_date,
        cast(null as Nullable(DateTime)) as departure_ts,
        cast(null as Nullable(DateTime)) as arrival_ts,
        cast(null as Nullable(Date)) as activity_date,
        cast(null as Nullable(String)) as seat_class,
        cast(null as Nullable(String)) as category,
        cast(guests as Nullable(UInt16)) as guests,
        cast(null as Nullable(UInt16)) as participants
    from {{ ref('silver_hotel_bookings') }}
),

flight as (
    select
        booking_ref as booking_id,
        'vendor:' || lower(trim(email)) as _lookup,
        'vendor_api' as source,
        'flight' as booking_type,
        airline as provider,
        destination as city,
        origin,
        destination,
        amount_idr,
        payment_method,
        booking_ts,
        booking_status as status,
        cast(null as Nullable(Date)) as check_in_date,
        cast(null as Nullable(Date)) as check_out_date,
        departure_ts,
        arrival_ts,
        cast(null as Nullable(Date)) as activity_date,
        seat_class,
        cast(null as Nullable(String)) as category,
        cast(null as Nullable(UInt16)) as guests,
        cast(null as Nullable(UInt16)) as participants
    from {{ ref('silver_flight_bookings') }}
),

experience as (
    select
        booking_ref as booking_id,
        'vendor:' || lower(trim(email)) as _lookup,
        'vendor_api' as source,
        'experience' as booking_type,
        experience_name as provider,
        city,
        cast(null as Nullable(String)) as origin,
        cast(null as Nullable(String)) as destination,
        amount_idr,
        payment_method,
        booking_ts,
        booking_status as status,
        cast(null as Nullable(Date)) as check_in_date,
        cast(null as Nullable(Date)) as check_out_date,
        cast(null as Nullable(DateTime)) as departure_ts,
        cast(null as Nullable(DateTime)) as arrival_ts,
        activity_date,
        cast(null as Nullable(String)) as seat_class,
        category,
        cast(null as Nullable(UInt16)) as guests,
        participants
    from {{ ref('silver_experience_bookings') }}
),

combined as (
    select * from hotel
    union all
    select * from flight
    union all
    select * from experience
),

resolved as (
    select
        c.booking_id,
        nullIf(dc.resolved_customer_id, '') as resolved_customer_id,
        nullIf(dc.identity_confidence, '') as identity_confidence,
        c.source,
        c.booking_type,
        c.provider,
        c.city,
        c.origin,
        c.destination,
        c.amount_idr,
        c.payment_method,
        c.booking_ts,
        c.status,
        c.check_in_date,
        c.check_out_date,
        c.departure_ts,
        c.arrival_ts,
        c.activity_date,
        c.seat_class,
        c.category,
        c.guests,
        c.participants
    from combined c
    left join (
        select resolved_customer_id, identity_confidence, arrayJoin(source_customer_ids) as scid
        from {{ ref('dim_customer') }}
    ) dc on dc.scid = c._lookup
)

select
    booking_id,
    resolved_customer_id,
    identity_confidence,
    source,
    booking_type,
    provider,
    city,
    origin,
    destination,
    amount_idr,
    payment_method,
    booking_ts,
    status,
    check_in_date,
    check_out_date,
    departure_ts,
    arrival_ts,
    activity_date,
    seat_class,
    category,
    guests,
    participants
from resolved
