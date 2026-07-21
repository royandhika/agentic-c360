import streamlit as st
import pandas as pd
from config import get_client
from labels import LABELS
from format import format_idr, tier_badge_html, confidence_badge_html
from queries.customer import search, total_count

L = LABELS["en"]

@st.cache_resource
def ch():
    return get_client()

st.title(L["customer_explorer"])

with st.sidebar:
    st.header("Filters")
    term = st.text_input("Search", placeholder="Name, email, phone, or ID...")
    tiers = st.multiselect("Loyalty Tier", ["gold", "silver", "churn_risk"], default=[])
    churn_range = st.slider("Churn Risk Score", 0.0, 1.0, (0.0, 1.0), step=0.05)
    actions = st.multiselect("Recommended Action", ["retain", "reengage", "cross_sell", "reactivate"], default=[])
    has_ticket = st.checkbox("Has support ticket", value=False)
    booking_range = st.slider("Distinct Booking Types", 0, 3, (0, 3))
    omnichannel = st.checkbox("Omnichannel only")
    sort_by = st.selectbox("Sort by", [
        "clv_desc", "churn_risk_desc", "dormant_desc", "last_booking_desc",
    ], format_func=lambda x: {
        "clv_desc": "CLV (highest)",
        "churn_risk_desc": "Churn Risk (highest)",
        "dormant_desc": "Dormant Days (most)",
        "last_booking_desc": "Last Booking (recent)",
    }.get(x, x))
    st.divider()
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        apply = st.button("Apply Filters", use_container_width=True)
    with btn_col2:
        reset = st.button("Reset", use_container_width=True)
    if reset:
        st.query_params.clear()
        st.rerun()

bt_min, bt_max = booking_range
bt_arg = [bt_min, bt_max] if bt_min != 0 or bt_max != 3 else []

if apply or True:
    df = search(ch(),
        term=term,
        tiers=tiers if tiers else None,
        churn_range=churn_range,
        actions=actions if actions else None,
        has_ticket=has_ticket if has_ticket else None,
        booking_types=bt_arg if bt_arg else None,
        omnichannel=omnichannel,
        sort_by=sort_by,
        limit=200,
    )
    total = total_count(ch(),
        term=term, tiers=tiers if tiers else None,
        churn_range=churn_range,
        actions=actions if actions else None,
        has_ticket=has_ticket if has_ticket else None,
        booking_types=bt_arg if bt_arg else None,
        omnichannel=omnichannel,
    )

    st.markdown(f"Showing **{len(df)}** of **{total}** customers")

    if len(df) == 0:
        st.info("No customers match these filters.")
    else:
        st.dataframe(
            df[[
                "name_std", "loyalty_tier", "clv_idr", "churn_risk_score",
                "booking_count", "completed_count", "cancelled_count",
                "dormant_days", "recommended_action", "has_support_ticket",
                "identity_confidence", "rcid_hex",
            ]].rename(columns={
                "name_std": "Name",
                "loyalty_tier": "Tier",
                "clv_idr": "CLV",
                "churn_risk_score": "Churn Risk",
                "booking_count": "Bookings",
                "completed_count": "Completed",
                "cancelled_count": "Cancelled",
                "dormant_days": "Dormant Days",
                "recommended_action": "Action",
                "has_support_ticket": "Has Tickets",
                "identity_confidence": "Confidence",
                "rcid_hex": "Customer ID",
            }),
            column_config={
                "CLV": st.column_config.NumberColumn(format="Rp %d"),
                "Churn Risk": st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=1),
                "Customer ID": st.column_config.TextColumn(width="small"),
            },
            hide_index=True,
            use_container_width=True,
            height=600,
        )

        st.markdown("---")
        st.markdown("#### Quick View — Select a Customer")
        selected_rcid = st.selectbox(
            "Choose a customer to view full 360 profile:",
            options=df["rcid_hex"].tolist(),
            format_func=lambda h: f"{df[df['rcid_hex'] == h]['name_std'].iloc[0]} ({h[:16]}...)",
        )
        if st.button("View Customer 360", type="primary"):
            st.query_params["rcid"] = selected_rcid
            st.switch_page("pages/3_Customer_360.py")
