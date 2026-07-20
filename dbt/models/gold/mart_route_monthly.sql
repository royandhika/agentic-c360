{{ config(materialized='incremental', unique_key='_pk') }}

with src as (
    select
        booking_type as route_type,
        if(booking_type = 'flight', concat(origin, '-', destination), city) as route_key,
        if(booking_type = 'flight', origin, null) as origin,
        if(booking_type = 'flight', destination, null) as destination,
        if(booking_type != 'flight', city, null) as city,
        toStartOfMonth(booking_ts) as year_month,
        concat(route_type, '|', route_key, '|', toString(year_month)) as _pk,
        amount_idr,
        booking_ts,
        status,
        seat_class,
        resolved_customer_id
    from {{ ref('fact_bookings') }}
),

agg as (
    select
        _pk,
        route_type,
        route_key,
        origin,
        destination,
        city,
        year_month,
        count() as booking_count,
        toUInt32(uniq(resolved_customer_id)) as unique_travelers,
        sum(amount_idr) as amount_idr_total,
        intDiv(sum(amount_idr), greatest(count(), 1)) as amount_idr_avg,
        if(route_type = 'flight',
           countIf(seat_class IN ('business', 'first')) / greatest(count(), 1),
           null) as business_class_share,
        countIf(status = 'cancelled') / greatest(count(), 1) as cancel_rate,
        countIf(status = 'no_show') / greatest(count(), 1) as no_show_rate
    from src
    group by _pk, route_type, route_key, origin, destination, city, year_month
)

select
    _pk,
    route_type,
    route_key,
    origin,
    destination,
    city,
    year_month,
    booking_count,
    unique_travelers,
    amount_idr_total,
    amount_idr_avg,
    business_class_share,
    cancel_rate,
    no_show_rate,
    multiIf(
        toString(year_month) IN ('2026-03-01', '2026-04-01'), 'lebaran',
        toString(year_month) IN ('2025-12-01', '2026-12-01'), 'natal',
        toString(year_month) = '2026-02-01', 'imlek',
        toString(year_month) IN ('2026-06-01', '2026-07-01', '2026-12-01'), 'school',
        'none'
    ) as holiday_window
from agg
