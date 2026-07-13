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

with email_failures as (
    select customer_id as entity_id, 'silver_customers' as source, email as bad_value
    from {{ ref('silver_customers') }}
    where email is not null and (email = '' or email not like '%@%.%')
    union all
    select booking_ref, 'silver_flight_bookings', email
    from {{ ref('silver_flight_bookings') }}
    where email is not null and (email = '' or email not like '%@%.%')
    union all
    select booking_ref, 'silver_experience_bookings', email
    from {{ ref('silver_experience_bookings') }}
    where email is not null and (email = '' or email not like '%@%.%')
    union all
    select ticket_id, 'silver_tickets', customer_email
    from {{ ref('silver_tickets') }}
    where customer_email is not null and (customer_email = '' or customer_email not like '%@%.%')
)
select * from email_failures
