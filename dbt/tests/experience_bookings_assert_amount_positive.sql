with amount_failures as (
    select booking_ref as entity_id, 'silver_experience_bookings' as source, toString(amount_idr) as bad_value
    from {{ ref('silver_experience_bookings') }}
    where amount_idr <= 0
)
select * from amount_failures
