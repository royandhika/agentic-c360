"""Reserved for Phase 6 LangChain tools. No implementations in v1."""

QUERY_TEMPLATES = {
    "tier_mix": "SELECT loyalty_tier, count() AS cnt FROM wanderfuel.dim_customer GROUP BY loyalty_tier",
    "top_customers": "SELECT resolved_customer_id, name_std, clv_idr FROM wanderfuel.dim_customer ORDER BY clv_idr DESC LIMIT 10",
    "customer_search": "SELECT * FROM wanderfuel.mart_customer_clv WHERE name_std ILIKE '%{term}%' LIMIT 5",
}

def get_tool_functions():
    """Return render-ready list of (name, description) for Phase 6 LangChain tool registration."""
    return [
        ("executive_kpi", "Get summary KPIs: total customers, avg CLV, total revenue, churn risk count, open tickets"),
        ("tier_mix", "Get loyalty tier distribution: gold, silver, churn_risk counts"),
        ("identity_funnel", "Get source-system combination breakdown"),
        ("revenue_by_type", "Get revenue broken down by booking type"),
        ("customer_search", "Search customers by name, email, phone, or ID"),
        ("customer_360", "Get full customer profile: identity, bookings, tickets"),
        ("route_table", "Get top routes/destinations by revenue"),
        ("monthly_trend", "Get monthly revenue trend by route"),
        ("holiday_comparison", "Get holiday-window revenue comparison"),
        ("business_class", "Get business-class share by flight route"),
    ]
