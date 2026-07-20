with phone_failures as (
    select customer_id as entity_id, 'silver_customers.phone' as check_name, phone as bad_value
    from {{ ref('silver_customers') }}
    where phone is not null and not match(phone, '^\\+62\\d+$')
)
select * from phone_failures
