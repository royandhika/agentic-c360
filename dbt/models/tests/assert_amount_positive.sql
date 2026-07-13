{{
    config(
        meta={
            'dagster': {
                'ref': {
                    'name': 'silver_hotel_bookings',
                    'package': 'wanderfuel_dbt_assets',
                    'version': 1,
                }
            }
        }
    )
}}

with amount_failures as (
    select booking_id as entity_id, 'silver_hotel_bookings' as source, toString(amount_idr) as bad_value
    from {{ ref('silver_hotel_bookings') }}
    where amount_idr <= 0
    union all
    select booking_ref, 'silver_flight_bookings', toString(amount_idr)
    from {{ ref('silver_flight_bookings') }}
    where amount_idr <= 0
    union all
    select booking_ref, 'silver_experience_bookings', toString(amount_idr)
    from {{ ref('silver_experience_bookings') }}
    where amount_idr <= 0
)
select * from amount_failures
