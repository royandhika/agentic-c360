with sentinel_failures as (
    select customer_id as entity_id, 'silver_customers.phone' as field, phone as bad_value
    from {{ ref('silver_customers') }}
    where phone in ('TIDAK ADA', '000-000-0000', '')
)
select * from sentinel_failures
