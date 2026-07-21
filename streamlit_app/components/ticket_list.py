import streamlit as st
import pandas as pd
from format import status_badge_html, priority_badge_html

def render(tickets_df: pd.DataFrame):
    if tickets_df is None or len(tickets_df) == 0:
        st.info("No support tickets for this customer.")
        return

    st.markdown("#### Support Tickets")
    for _, row in tickets_df.head(20).iterrows():
        with st.expander(f"**{row['subject']}** — {row['status']} ({row['priority']})"):
            c1, c2, c3 = st.columns([1, 1, 1])
            c1.markdown(status_badge_html(row["status"]), unsafe_allow_html=True)
            c2.markdown(priority_badge_html(row["priority"]), unsafe_allow_html=True)
            c3.markdown(f"**{row['category']}** · {row['channel']}")
            st.caption(f"Created: {row['created_at']} | Agent: {row['agent_name']}")
            if pd.notna(row.get("resolved_at")):
                st.caption(f"Resolved: {row['resolved_at']}")
            st.markdown(f"> {row['body']}")
