{{
    config(
        meta={
            'dagster': {
                'ref': {
                    'name': 'silver_customers',
                    'package': 'wanderfuel_dbt_assets',
                    'version': 1,
                }
            }
        }
    )
}}

with phone_failures as (
    select customer_id as entity_id, 'silver_customers.phone' as check_name, phone as bad_value
    from {{ ref('silver_customers') }}
    where phone is not null and not match(phone, '^\\+62\\d+$')
    union all
    select ticket_id, 'silver_tickets.customer_phone', customer_phone
    from {{ ref('silver_tickets') }}
    where customer_phone is not null and not match(customer_phone, '^\\+62\\d+$')
)
select * from phone_failures
