import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from config import get_client
from labels import LABELS
from format import format_idr, tier_badge_html
from queries.executive import (
    kpi_summary, identity_funnel, tier_mix, revenue_by_type,
    monthly_revenue, top_destinations, top_customers, city_revenue_for_map,
)
from components.kpi_cards import kpi_row
from components.route_map import render as render_map
from components.ai_slots import alert_banner_slot, nl_query_box

L = LABELS["en"]

@st.cache_resource
def ch():
    return get_client()

st.title(L["executive_overview"])

ai_alert = alert_banner_slot()
nl_box = nl_query_box()

kpi = kpi_summary(ch())
churn_pct = (kpi["churn_risk_count"] / max(kpi["total_customers"], 1)) * 100

kpi_row([
    {"label": L["total_customers"], "value": kpi["total_customers"], "fmt": "number"},
    {"label": L["avg_clv"], "value": kpi["avg_clv"], "fmt": "idr"},
    {"label": L["total_revenue"], "value": kpi["total_revenue"], "fmt": "idr"},
    {"label": L["churn_risk"], "value": kpi["churn_risk_count"], "fmt": "number", "suffix": f" ({churn_pct:.1f}%)"},
    {"label": L["open_tickets"], "value": kpi["open_tickets"], "fmt": "number", "suffix": f" ({kpi['critical_tickets']} critical)"},
])

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Identity Resolution Funnel")
    df_funnel = identity_funnel(ch())
    fig_funnel = px.bar(
        df_funnel, x="cnt", y="combo", orientation="h",
        title="Customers by Source Combination",
        color_discrete_sequence=["#6366f1"],
        template="plotly_dark",
    )
    fig_funnel.update_layout(showlegend=False)
    st.plotly_chart(fig_funnel, use_container_width=True)

with col2:
    st.subheader("Loyalty Tier Mix")
    df_tier = tier_mix(ch())
    fig_tier = go.Figure(data=[go.Pie(
        labels=df_tier["loyalty_tier"],
        values=df_tier["cnt"],
        hole=0.6,
        marker=dict(colors=["#f0b429", "#94a3b8", "#f87171"]),
    )])
    fig_tier.update_layout(template="plotly_dark")
    st.plotly_chart(fig_tier, use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    st.subheader("Revenue by Booking Type")
    df_rev = revenue_by_type(ch())
    fig_rev = px.bar(
        df_rev, x="booking_type", y="total_revenue",
        color="booking_type",
        color_discrete_map={"hotel": "#6366f1", "flight": "#22d3ee", "experience": "#f0b429"},
        template="plotly_dark",
    )
    fig_rev.update_layout(showlegend=False)
    st.plotly_chart(fig_rev, use_container_width=True)

with col4:
    st.subheader("Monthly Revenue Trend")
    df_monthly = monthly_revenue(ch())
    fig_monthly = px.line(
        df_monthly, x="year_month", y="total_revenue",
        markers=True, template="plotly_dark",
    )
    fig_monthly.update_traces(line=dict(color="#22d3ee"))
    st.plotly_chart(fig_monthly, use_container_width=True)

st.subheader("Top 10 Destinations by Revenue")
df_dest = top_destinations(ch(), limit=10)
fig_dest = px.bar(
    df_dest, x="total_revenue", y="city", orientation="h",
    color="peak_holiday", template="plotly_dark",
    color_discrete_sequence=px.colors.qualitative.Bold,
)
st.plotly_chart(fig_dest, use_container_width=True)

st.subheader("Indonesia Revenue Map")
df_map = city_revenue_for_map(ch())
fig_map = render_map(df_map)
st.plotly_chart(fig_map, use_container_width=True)

st.subheader("Top 10 Customers by CLV")
df_top = top_customers(ch(), limit=10)
cols = st.columns([3, 2, 1, 2, 1])
cols[0].markdown("**Name**")
cols[1].markdown("**Tier**")
cols[2].markdown("**CLV**")
cols[3].markdown("**Email**")
cols[4].markdown("**Actions**")
for _, row in df_top.iterrows():
    c1, c2, c3, c4, c5 = st.columns([3, 2, 1, 2, 1])
    c1.write(row["name_std"] or "—")
    c2.markdown(tier_badge_html(row["loyalty_tier"]), unsafe_allow_html=True)
    c3.write(format_idr(row["clv_idr"]))
    emails = row["emails"]
    c4.write(emails[0] if emails else "—")
    if c5.button("View", key=f"exec_view_{row['rcid_hex']}"):
        st.query_params["rcid"] = row["rcid_hex"]
        st.switch_page("pages/3_Customer_360.py")
