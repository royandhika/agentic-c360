import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from config import get_client
from labels import LABELS
from format import format_idr, tier_badge_html
from queries.customer_360 import fetch as fetch_360
from components.identity_panel import render as render_identity
from components.booking_timeline import render as render_timeline
from components.ticket_list import render as render_tickets
from components.ai_slots import insight_summary_slot, anomaly_explainer_slot, recommended_action_card

L = LABELS["en"]

@st.cache_resource
def ch():
    return get_client()

rcid = st.query_params.get("rcid", None)

if not rcid:
    st.title(L["customer_360"])
    st.info(L["no_customer_selected"])
    st.stop()

data = fetch_360(ch(), rcid)
if data["customer"] is None:
    st.error(f"Customer not found: `{rcid}`")
    st.stop()

cust = data["customer"]
mcl = data["mcl"]
bookings = data["bookings"]
tickets = data["tickets"]

st.title(cust[3] or "Unknown Customer")

if st.button(L["back_to_explorer"]):
    st.query_params.clear()
    st.switch_page("pages/2_Customer_Explorer.py")

st.divider()

render_identity(cust, mcl)

ai_insight = insight_summary_slot(rcid)
ai_anomaly = anomaly_explainer_slot(rcid)

with ai_insight:
    if mcl:
        action = mcl[15] or "reengage"
        st.info(f"**{L['recommended_action']}:** {L.get(action, action)} — Churn score: {mcl[10]:.2f}")

with ai_anomaly:
    with st.container():
        pass

col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("Booking Timeline")
    if bookings is not None and len(bookings) > 0:
        fig_timeline = render_timeline(bookings)
        st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.info("No bookings found.")

with col_right:
    ai_action = recommended_action_card(rcid)
    with ai_action:
        if mcl:
            action = mcl[15] or "reengage"
            st.metric("Churn Risk Score", f"{mcl[10]:.2f}" if mcl else "N/A")
            st.metric("Recommended Action", L.get(action, action))
            st.metric("Dormant Days", mcl[8] or 0)
    
    if bookings is not None and len(bookings) > 0:
        st.subheader("Booking Mix")
        type_counts = bookings["booking_type"].value_counts()
        fig_mix = go.Figure(data=[go.Pie(
            labels=type_counts.index,
            values=type_counts.values,
            hole=0.5,
            marker=dict(colors=["#6366f1", "#22d3ee", "#f0b429"]),
        )])
        fig_mix.update_layout(template="plotly_dark", height=300)
        st.plotly_chart(fig_mix, use_container_width=True)

st.divider()

if bookings is not None and len(bookings) > 0:
    st.subheader("Recent Bookings")
    disp = bookings.head(10).copy()
    disp["amount_idr"] = disp["amount_idr"].apply(format_idr)
    st.dataframe(
        disp[[
            "booking_id", "booking_type", "provider", "city",
            "origin", "destination", "amount_idr", "status",
            "payment_method", "booking_ts",
        ]].rename(columns={
            "booking_id": "Booking ID",
            "booking_type": "Type",
            "provider": "Provider",
            "city": "City",
            "origin": "From",
            "destination": "To",
            "amount_idr": "Amount",
            "status": "Status",
            "payment_method": "Payment",
            "booking_ts": "Date",
        }),
        hide_index=True,
        use_container_width=True,
    )

st.divider()

render_tickets(tickets)

st.divider()

if mcl:
    distinct = mcl[14] or 0
    if distinct == 1:
        all_types = ["hotel", "flight", "experience"]
        booked = bookings["booking_type"].iloc[0] if len(bookings) > 0 else "unknown"
        missing = [t for t in all_types if t != booked]
        st.warning(f"This customer only books **{booked}**. Cross-sell opportunities: {', '.join(missing)}.")
    elif distinct == 3:
        st.success("This customer books across all categories.")
    else:
        st.info(f"This customer books {distinct} of 3 categories.")
