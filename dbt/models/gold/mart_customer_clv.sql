{{ config(materialized='incremental', unique_key='resolved_customer_id') }}

with bookings_agg as (
    select
        resolved_customer_id,
        sum(if(status = 'completed', amount_idr, 0)) as clv_idr,
        countIf(status = 'completed') as completed_count,
        countIf(status = 'cancelled') as cancelled_count,
        countIf(status = 'no_show') as no_show_count,
        count() as booking_count,
        max(booking_ts) as last_booking_ts,
        toUInt8(uniq(booking_type)) as distinct_booking_types,
        argMax(booking_type, booking_ts) as most_recent_booking_type
    from {{ ref('fact_bookings') }}
    group by resolved_customer_id
),

customer_scids as (
    select resolved_customer_id, arrayJoin(source_customer_ids) as scid
    from {{ ref('dim_customer') }}
),

support_agg as (
    select
        ct.resolved_customer_id,
        uniqIf(st.ticket_id, st.priority = 'critical') as critical_ticket_count,
        avg(dateDiff('hour', st.created_at, st.resolved_at)) as avg_resolution_hours,
        toUInt8(1) as has_support_ticket
    from customer_scids ct
    inner join {{ ref('silver_tickets') }} st
        on ct.scid = concat('crm:', st.ticket_id)
    group by ct.resolved_customer_id
),

enriched as (
    select
        dc.resolved_customer_id as resolved_customer_id,
        coalesce(ba.clv_idr, toInt64(0)) as clv_idr,
        coalesce(ba.completed_count, toUInt32(0)) as completed_count,
        coalesce(ba.cancelled_count, toUInt32(0)) as cancelled_count,
        coalesce(ba.no_show_count, toUInt32(0)) as no_show_count,
        coalesce(ba.booking_count, toUInt32(0)) as booking_count,
        ba.last_booking_ts,
        dc.dormant_days,
        dc.loyalty_tier,
        coalesce(sa.critical_ticket_count, toUInt32(0)) as critical_ticket_count,
        coalesce(sa.has_support_ticket, toUInt8(0)) as has_support_ticket,
        sa.avg_resolution_hours,
        coalesce(ba.distinct_booking_types, toUInt8(0)) as distinct_booking_types,
        ba.most_recent_booking_type,
        if(completed_count > 0, intDiv(clv_idr, toInt64(completed_count)), toInt64(0)) as aov_idr
    from {{ ref('dim_customer') }} dc
    left join bookings_agg ba on dc.resolved_customer_id = ba.resolved_customer_id
    left join support_agg sa on dc.resolved_customer_id = sa.resolved_customer_id
),

scored as (
    select
        resolved_customer_id,
        clv_idr,
        aov_idr,
        booking_count,
        completed_count,
        cancelled_count,
        no_show_count,
        last_booking_ts,
        dormant_days,
        loyalty_tier,
        has_support_ticket,
        critical_ticket_count,
        avg_resolution_hours,
        distinct_booking_types,
        most_recent_booking_type,
        greatest(0.0, least(1.0,
            0.40 * if(clv_idr < 2000000, 1.0, if(clv_idr >= 10000000, 0.0, 1.0 - (clv_idr - 2000000) / 8000000.0))
            + 0.40 * least(toFloat64(dormant_days) / 180.0, 1.0)
            + 0.15 * (cancelled_count + no_show_count) / greatest(booking_count, 1)
            + 0.05 * least(critical_ticket_count / 3.0, 1.0)
        )) as churn_risk_score
    from enriched
),

actioned as (
    select
        resolved_customer_id,
        clv_idr,
        aov_idr,
        booking_count,
        completed_count,
        cancelled_count,
        no_show_count,
        last_booking_ts,
        dormant_days,
        loyalty_tier,
        churn_risk_score,
        has_support_ticket,
        critical_ticket_count,
        avg_resolution_hours,
        distinct_booking_types,
        multiIf(
            churn_risk_score >= 0.7, 'reactivate',
            distinct_booking_types = 1 AND most_recent_booking_type = 'flight', 'cross_sell',
            loyalty_tier = 'gold' AND churn_risk_score < 0.3, 'retain',
            'reengage'
        ) as recommended_action
    from scored
)

select
    resolved_customer_id,
    clv_idr,
    aov_idr,
    booking_count,
    completed_count,
    cancelled_count,
    no_show_count,
    last_booking_ts,
    dormant_days,
    loyalty_tier,
    churn_risk_score,
    has_support_ticket,
    critical_ticket_count,
    avg_resolution_hours,
    distinct_booking_types,
    recommended_action
from actioned
