with email_failures as (
    select ticket_id as entity_id, 'silver_tickets' as source, customer_email as bad_value
    from {{ ref('silver_tickets') }}
    where customer_email is not null and (customer_email = '' or customer_email not like '%@%.%')
)
select * from email_failures
