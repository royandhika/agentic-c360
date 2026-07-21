import pandas as pd
from clickhouse_connect.driver import Client
from queries._filters import build_where_clause, build_order_clause

def search(ch: Client, *, term="", limit=100, tiers=None, churn_range=None,
           actions=None, has_ticket=None, booking_types=None,
           omnichannel=False, sort_by="clv_desc") -> pd.DataFrame:
    where = build_where_clause(
        term=term, tiers=tiers, churn_range=churn_range,
        actions=actions, has_ticket=has_ticket,
        booking_types=booking_types, omnichannel=omnichannel,
    )
    order = build_order_clause(sort_by)

    query = f"""
        SELECT
            mcl.resolved_customer_id,
            hex(dc.resolved_customer_id) AS rcid_hex,
            dc.name_std,
            mcl.loyalty_tier,
            mcl.clv_idr,
            mcl.churn_risk_score,
            mcl.booking_count,
            mcl.completed_count,
            mcl.cancelled_count,
            mcl.dormant_days,
            mcl.last_booking_ts,
            mcl.recommended_action,
            mcl.has_support_ticket,
            mcl.critical_ticket_count,
            mcl.distinct_booking_types,
            dc.emails,
            dc.phones,
            dc.source_systems,
            dc.identity_confidence
        FROM wanderfuel.mart_customer_clv mcl
        JOIN wanderfuel.dim_customer dc USING (resolved_customer_id)
        WHERE {where}
        ORDER BY {order}
        LIMIT %(limit)s
    """
    return ch.query_df(query, parameters={"limit": limit})

def total_count(ch: Client, *, term="", tiers=None, churn_range=None,
                actions=None, has_ticket=None, booking_types=None,
                omnichannel=False) -> int:
    where = build_where_clause(
        term=term, tiers=tiers, churn_range=churn_range,
        actions=actions, has_ticket=has_ticket,
        booking_types=booking_types, omnichannel=omnichannel,
    )
    row = ch.query(f"""
        SELECT count()
        FROM wanderfuel.mart_customer_clv mcl
        JOIN wanderfuel.dim_customer dc USING (resolved_customer_id)
        WHERE {where}
    """).first_row
    return row[0] if row else 0
