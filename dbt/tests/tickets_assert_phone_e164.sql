with phone_failures as (
    select ticket_id as entity_id, 'silver_tickets.customer_phone' as check_name, customer_phone as bad_value
    from {{ ref('silver_tickets') }}
    where customer_phone is not null and not match(customer_phone, '^\\+62\\d+$')
)
select * from phone_failures
