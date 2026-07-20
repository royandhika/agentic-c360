{{ config(materialized='incremental', unique_key='resolved_customer_id') }}

with all_emails as (
    select email from {{ ref('silver_customers') }} where email is not null and email != ''
    union distinct
    select email from {{ ref('silver_flight_bookings') }} where email is not null and email != ''
    union distinct
    select email from {{ ref('silver_experience_bookings') }} where email is not null and email != ''
    union distinct
    select customer_email as email from {{ ref('silver_tickets') }} where customer_email is not null and customer_email != ''
),

email_lookup as (
    select
        email,
        'rc_' || substr(MD5(lower(trim(email))), 1, 12) as resolved_customer_id
    from all_emails
),

app_anchors as (
    select
        el.resolved_customer_id,
        sc.customer_id,
        sc.email,
        sc.phone,
        sc.full_name as name_std,
        sc.city as address_city,
        sc.province as address_province,
        sc.postal_code as address_postal_code,
        sc.created_at as first_seen,
        coalesce(sc.updated_at, sc.created_at) as last_seen,
        'app:' || sc.customer_id as source_customer_id_expr,
        'app_oltp' as source_system,
        3 as confidence_rank
    from {{ ref('silver_customers') }} sc
    inner join email_lookup el on sc.email = el.email
),

vendor_emails as (
    select email, booking_ts from {{ ref('silver_flight_bookings') }}
    union all
    select email, booking_ts from {{ ref('silver_experience_bookings') }}
),

vendor_grouped as (
    select
        email,
        min(booking_ts) as first_seen,
        max(booking_ts) as last_seen
    from vendor_emails
    where email is not null and email != ''
    group by email
),

vendor_identities as (
    select
        el.resolved_customer_id,
        vg.email,
        '' as phone,
        null as name_std,
        null as address_city,
        null as address_province,
        null as address_postal_code,
        vg.first_seen,
        vg.last_seen,
        'vendor:' || vg.email as source_customer_id_expr,
        'vendor_api' as source_system,
        1 as confidence_rank
    from vendor_grouped vg
    inner join email_lookup el on vg.email = el.email
    where vg.email not in (select email from app_anchors)
),

vendor_links as (
    select
        aa.resolved_customer_id as resolved_customer_id,
        aa.email as email,
        cast('' as String) as phone,
        aa.name_std as name_std,
        aa.address_city as address_city,
        aa.address_province as address_province,
        aa.address_postal_code as address_postal_code,
        vg.first_seen as first_seen,
        vg.last_seen as last_seen,
        'vendor:' || aa.email as source_customer_id_expr,
        'vendor_api' as source_system,
        3 as confidence_rank
    from app_anchors aa
    inner join vendor_grouped vg on aa.email = vg.email
),

crm_candidates as (
    select
        coalesce(aa.resolved_customer_id, aa2.resolved_customer_id, vi.resolved_customer_id, el.resolved_customer_id) as resolved_customer_id,
        st.ticket_id,
        st.customer_email,
        st.customer_phone,
        st.customer_name as name_std,
        null as address_city,
        null as address_province,
        null as address_postal_code,
        st.created_at as first_seen,
        st.created_at as last_seen,
        'crm:' || st.ticket_id as source_customer_id_expr,
        'crm' as source_system,
        multiIf(
            aa.resolved_customer_id is not null, 3,
            aa2.resolved_customer_id is not null, 2,
            1
        ) as confidence_rank
    from {{ ref('silver_tickets') }} st
    left join app_anchors aa on st.customer_email = aa.email
    left join app_anchors aa2 on st.customer_phone = aa2.phone and st.customer_phone != '' and st.customer_phone != ''
    left join vendor_identities vi on st.customer_email = vi.email
    left join email_lookup el on st.customer_email = el.email
),

identity_rows as (
    select resolved_customer_id, source_customer_id_expr, source_system, confidence_rank, first_seen, last_seen, email, phone, name_std, address_city, address_province, address_postal_code from app_anchors
    union all
    select resolved_customer_id, source_customer_id_expr, source_system, confidence_rank, first_seen, last_seen, email, phone, name_std, address_city, address_province, address_postal_code from vendor_identities
    union all
    select resolved_customer_id, source_customer_id_expr, source_system, confidence_rank, first_seen, last_seen, email, cast('' as String) as phone, name_std, address_city, address_province, address_postal_code from vendor_links
    union all
    select resolved_customer_id, source_customer_id_expr, source_system, confidence_rank, first_seen, last_seen, customer_email as email, customer_phone as phone, name_std, address_city, address_province, address_postal_code from crm_candidates
),

clv_by_resolved as (
    select
        ir.resolved_customer_id,
        coalesce(sum(sb.amount_idr), 0) as clv_idr
    from identity_rows ir
    left join (
        select 'app:' || customer_id as scid, amount_idr from {{ ref('silver_hotel_bookings') }} where booking_status = 'completed'
        union all
        select 'vendor:' || email as scid, amount_idr from {{ ref('silver_flight_bookings') }} where booking_status = 'completed'
        union all
        select 'vendor:' || email as scid, amount_idr from {{ ref('silver_experience_bookings') }} where booking_status = 'completed'
    ) sb on ir.source_customer_id_expr = sb.scid
    group by ir.resolved_customer_id
),

aggregated as (
    select
        ir.resolved_customer_id,
        arraySort(arrayDistinct(groupArrayIf(ir.email, ir.email != ''))) as emails,
        arraySort(arrayDistinct(groupArrayIf(ir.phone, ir.phone != ''))) as phones,
        arraySort(arrayDistinct(groupArray(ir.source_customer_id_expr))) as source_customer_ids,
        arraySort(arrayDistinct(groupArray(ir.source_system))) as source_systems,
        min(ir.first_seen) as first_seen,
        max(ir.last_seen) as last_seen,
        toUInt32(dateDiff('day', max(ir.last_seen), today())) as dormant_days,
        argMax(ir.name_std, ir.confidence_rank) as name_std,
        argMax(ir.address_city, ir.confidence_rank) as address_city,
        argMax(ir.address_province, ir.confidence_rank) as address_province,
        argMax(ir.address_postal_code, ir.confidence_rank) as address_postal_code,
        max(ir.confidence_rank) as max_rank
    from identity_rows ir
    group by ir.resolved_customer_id
),

tiered as (
    select
        agg.resolved_customer_id,
        agg.emails,
        agg.phones,
        agg.name_std,
        agg.address_city,
        agg.address_province,
        agg.address_postal_code,
        agg.source_customer_ids,
        agg.source_systems,
        agg.first_seen,
        agg.last_seen,
        agg.dormant_days,
        multiIf(agg.max_rank = 3, 'high', agg.max_rank = 2, 'phone_bridge', 'email') as identity_confidence,
        coalesce(clv.clv_idr, toInt64(0)) as clv_idr,
        multiIf(
            agg.dormant_days > 90, 'churn_risk',
            coalesce(clv.clv_idr, toInt64(0)) >= 10000000, 'gold',
            coalesce(clv.clv_idr, toInt64(0)) >= 2000000, 'silver',
            'churn_risk'
        ) as loyalty_tier
    from aggregated agg
    left join clv_by_resolved clv on agg.resolved_customer_id = clv.resolved_customer_id
)

select
    resolved_customer_id,
    emails,
    phones,
    name_std,
    address_city,
    address_province,
    address_postal_code,
    source_customer_ids,
    source_systems,
    first_seen,
    last_seen,
    dormant_days,
    identity_confidence,
    clv_idr,
    loyalty_tier
from tiered
