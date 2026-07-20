with amount_failures as (
    select booking_id as entity_id, 'silver_hotel_bookings' as source, toString(amount_idr) as bad_value
    from {{ ref('silver_hotel_bookings') }}
    where amount_idr <= 0
)
select * from amount_failures
