import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from config import get_client
from labels import LABELS
from format import format_idr
from queries.routes import route_table, monthly_trend, holiday_comparison, business_class_share

L = LABELS["en"]

@st.cache_resource
def ch():
    return get_client()

st.title(L["route_analytics"])

col1, col2, col3 = st.columns(3)
with col1:
    route_type = st.selectbox("Route Type", ["all", "flight", "hotel", "experience"], index=0)
with col2:
    top_n = st.selectbox("Top Routes", [10, 20, 50], index=1)
with col3:
    st.write("")

rt = None if route_type == "all" else route_type

df_routes = route_table(ch(), route_type=rt, limit=top_n)

st.subheader(f"Top {top_n} Routes/Destinations")
st.dataframe(
    df_routes[[
        "route_key", "route_type", "booking_count", "unique_travelers",
        "amount_idr_total", "amount_idr_avg", "cancel_rate", "no_show_rate",
        "business_class_share",
    ]].rename(columns={
        "route_key": "Route",
        "route_type": "Type",
        "booking_count": "Bookings",
        "unique_travelers": "Travelers",
        "amount_idr_total": "Total Revenue",
        "amount_idr_avg": "Avg Revenue",
        "cancel_rate": "Cancel %",
        "no_show_rate": "No-Show %",
        "business_class_share": "Business %",
    }),
    column_config={
        "Total Revenue": st.column_config.NumberColumn(format="Rp %d"),
        "Avg Revenue": st.column_config.NumberColumn(format="Rp %d"),
        "Cancel %": st.column_config.NumberColumn(format="%.1f%%"),
        "No-Show %": st.column_config.NumberColumn(format="%.1f%%"),
        "Business %": st.column_config.NumberColumn(format="%.1f%%"),
    },
    hide_index=True,
    use_container_width=True,
    height=500,
)

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Monthly Revenue Trend")
    df_trend = monthly_trend(ch(), route_type=rt, top_n=5)
    fig_trend = px.line(
        df_trend, x="year_month", y="amount_idr_total", color="route_key",
        markers=True, template="plotly_dark",
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with col_b:
    st.subheader("Holiday-Window Comparison")
    df_holiday = holiday_comparison(ch(), route_type=rt)
    fig_hol = px.bar(
        df_holiday, x="holiday_window", y="total_revenue",
        color="holiday_window", template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    fig_hol.update_layout(showlegend=False)
    st.plotly_chart(fig_hol, use_container_width=True)

if route_type == "all" or route_type == "flight":
    st.subheader("Business Class Share — Top Flight Routes")
    df_biz = business_class_share(ch())
    fig_biz = px.bar(
        df_biz, x="business_class_share", y="route_key", orientation="h",
        template="plotly_dark", title="Business/First Class Share by Route",
        color_discrete_sequence=["#f0b429"],
    )
    st.plotly_chart(fig_biz, use_container_width=True)
