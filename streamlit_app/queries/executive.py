import pandas as pd
from clickhouse_connect.driver import Client

def kpi_summary(ch: Client) -> dict:
    row = ch.query("""
        SELECT
            (SELECT count() FROM wanderfuel.dim_customer) AS total_customers,
            (SELECT round(avg(clv_idr)) FROM wanderfuel.dim_customer WHERE clv_idr > 0) AS avg_clv,
            (SELECT coalesce(sum(amount_idr), 0) FROM wanderfuel.fact_bookings WHERE status = 'completed') AS total_revenue,
            (SELECT count() FROM wanderfuel.dim_customer WHERE loyalty_tier = 'churn_risk') AS churn_risk_count,
            (SELECT count() FROM wanderfuel.silver_tickets WHERE status IN ('open', 'in_progress')) AS open_tickets,
            (SELECT count() FROM wanderfuel.silver_tickets WHERE status IN ('open', 'in_progress') AND priority = 'critical') AS critical_tickets
    """).first_row
    return {
        "total_customers": row[0],
        "avg_clv": row[1],
        "total_revenue": row[2],
        "churn_risk_count": row[3],
        "open_tickets": row[4],
        "critical_tickets": row[5],
    }

def identity_funnel(ch: Client) -> pd.DataFrame:
    return ch.query_df("""
        SELECT
            arrayStringConcat(arraySort(source_systems), ', ') AS combo,
            count() AS cnt
        FROM wanderfuel.dim_customer
        GROUP BY source_systems
        ORDER BY cnt DESC
    """)

def tier_mix(ch: Client) -> pd.DataFrame:
    return ch.query_df("""
        SELECT
            loyalty_tier,
            count() AS cnt,
            round(avg(clv_idr)) AS avg_clv
        FROM wanderfuel.dim_customer
        GROUP BY loyalty_tier
        ORDER BY avg_clv DESC
    """)

def revenue_by_type(ch: Client) -> pd.DataFrame:
    return ch.query_df("""
        SELECT
            booking_type,
            count() AS cnt,
            coalesce(sum(amount_idr), 0) AS total_revenue
        FROM wanderfuel.fact_bookings
        WHERE status = 'completed'
        GROUP BY booking_type
        ORDER BY total_revenue DESC
    """)

def monthly_revenue(ch: Client) -> pd.DataFrame:
    return ch.query_df("""
        SELECT
            year_month,
            sum(amount_idr_total) AS total_revenue
        FROM wanderfuel.mart_route_monthly
        GROUP BY year_month
        ORDER BY year_month
    """)

def top_destinations(ch: Client, limit: int = 10) -> pd.DataFrame:
    return ch.query_df("""
        SELECT
            city,
            sum(amount_idr_total) AS total_revenue,
            sum(booking_count) AS booking_count,
            any(holiday_window) AS peak_holiday
        FROM wanderfuel.mart_route_monthly
        WHERE city IS NOT NULL AND city != ''
        GROUP BY city
        ORDER BY total_revenue DESC
        LIMIT %(limit)s
    """, parameters={"limit": limit})

def top_customers(ch: Client, limit: int = 10) -> pd.DataFrame:
    return ch.query_df("""
        SELECT
            resolved_customer_id,
            hex(resolved_customer_id) AS rcid_hex,
            name_std,
            loyalty_tier,
            clv_idr,
            emails,
            phones,
            dormant_days,
            source_systems
        FROM wanderfuel.dim_customer
        ORDER BY clv_idr DESC
        LIMIT %(limit)s
    """, parameters={"limit": limit})

def city_revenue_for_map(ch: Client) -> pd.DataFrame:
    return ch.query_df("""
        SELECT
            city,
            sum(amount_idr_total) AS total_revenue,
            sum(booking_count) AS booking_count
        FROM wanderfuel.mart_route_monthly
        WHERE city IS NOT NULL AND city != ''
        GROUP BY city
        ORDER BY total_revenue DESC
    """)
