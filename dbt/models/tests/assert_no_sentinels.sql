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

with sentinel_failures as (
    select customer_id as entity_id, 'silver_customers.phone' as field, phone as bad_value
    from {{ ref('silver_customers') }}
    where phone in ('TIDAK ADA', '000-000-0000', '')
    union all
    select ticket_id, 'silver_tickets.customer_phone', customer_phone
    from {{ ref('silver_tickets') }}
    where customer_phone in ('TIDAK ADA', '000-000-0000', '')
)
select * from sentinel_failures
