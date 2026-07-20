with email_failures as (
    select customer_id as entity_id, 'silver_customers' as source, email as bad_value
    from {{ ref('silver_customers') }}
    where email is not null and (email = '' or email not like '%@%.%')
)
select * from email_failures
