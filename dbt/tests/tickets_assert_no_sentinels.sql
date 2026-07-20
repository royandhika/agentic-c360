with sentinel_failures as (
    select ticket_id as entity_id, 'silver_tickets.customer_phone' as field, customer_phone as bad_value
    from {{ ref('silver_tickets') }}
    where customer_phone in ('TIDAK ADA', '000-000-0000', '')
)
select * from sentinel_failures
