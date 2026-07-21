import pandas as pd
from clickhouse_connect.driver import Client

def route_table(ch: Client, *, route_type=None, limit=50) -> pd.DataFrame:
    type_filter = "1=1"
    params = {"limit": limit}
    if route_type and route_type != "all":
        type_filter = "route_type = %(route_type)s"
        params["route_type"] = route_type

    return ch.query_df(f"""
        SELECT
            route_key,
            route_type,
            origin,
            destination,
            city,
            sum(booking_count) AS booking_count,
            sum(unique_travelers) AS unique_travelers,
            sum(amount_idr_total) AS amount_idr_total,
            intDiv(sum(amount_idr_total), greatest(sum(booking_count), 1)) AS amount_idr_avg,
            avg(cancel_rate) AS cancel_rate,
            avg(no_show_rate) AS no_show_rate,
            any(holiday_window) AS peak_holiday,
            avg(business_class_share) AS business_class_share
        FROM wanderfuel.mart_route_monthly
        WHERE {type_filter}
        GROUP BY route_key, route_type, origin, destination, city
        ORDER BY amount_idr_total DESC
        LIMIT %(limit)s
    """, parameters=params)

def monthly_trend(ch: Client, *, route_type=None, top_n=5) -> pd.DataFrame:
    type_filter = "1=1"
    params = {"top_n": top_n}
    if route_type and route_type != "all":
        type_filter = "route_type = %(route_type)s"
        params["route_type"] = route_type

    return ch.query_df(f"""
        WITH top_routes AS (
            SELECT route_key
            FROM wanderfuel.mart_route_monthly
            WHERE {type_filter}
            GROUP BY route_key
            ORDER BY sum(amount_idr_total) DESC
            LIMIT %(top_n)s
        )
        SELECT
            mrm.year_month,
            CASE WHEN tr.route_key IS NOT NULL THEN mrm.route_key ELSE 'Other' END AS route_key,
            sum(mrm.amount_idr_total) AS amount_idr_total,
            sum(mrm.booking_count) AS booking_count
        FROM wanderfuel.mart_route_monthly mrm
        LEFT JOIN top_routes tr ON mrm.route_key = tr.route_key
        WHERE {type_filter}
        GROUP BY year_month,
            CASE WHEN tr.route_key IS NOT NULL THEN mrm.route_key ELSE 'Other' END
        ORDER BY year_month, amount_idr_total DESC
    """, parameters=params)

def holiday_comparison(ch: Client, *, route_type=None) -> pd.DataFrame:
    type_filter = "1=1"
    params = {}
    if route_type and route_type != "all":
        type_filter = "route_type = %(route_type)s"
        params["route_type"] = route_type

    return ch.query_df(f"""
        SELECT
            holiday_window,
            sum(amount_idr_total) AS total_revenue,
            sum(booking_count) AS booking_count
        FROM wanderfuel.mart_route_monthly
        WHERE {type_filter} AND holiday_window != ''
        GROUP BY holiday_window
        ORDER BY total_revenue DESC
    """, parameters=params)

def business_class_share(ch: Client) -> pd.DataFrame:
    return ch.query_df("""
        SELECT
            route_key,
            avg(business_class_share) AS business_class_share,
            sum(booking_count) AS booking_count
        FROM wanderfuel.mart_route_monthly
        WHERE route_type = 'flight' AND business_class_share IS NOT NULL
        GROUP BY route_key
        ORDER BY business_class_share DESC
        LIMIT 15
    """)
