with email_failures as (
    select booking_ref as entity_id, 'silver_experience_bookings' as source, email as bad_value
    from {{ ref('silver_experience_bookings') }}
    where email is not null and (email = '' or email not like '%@%.%')
)
select * from email_failures
