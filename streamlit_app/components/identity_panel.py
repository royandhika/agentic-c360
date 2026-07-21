import streamlit as st
from format import format_idr, tier_badge_html, confidence_badge_html, format_phone, SHORT_PHONE

def render(customer_row, mcl_row):
    """Render identity resolution panel for a single customer."""
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        name = customer_row[3] or "Unknown"
        st.markdown(f"### {name}")
        rcid = customer_row[0]
        st.caption(f"ID: `{rcid}`")

    with col2:
        tier = customer_row[14] or "basic"
        st.markdown(tier_badge_html(tier), unsafe_allow_html=True)
        conf = customer_row[12] or "email"
        st.markdown(confidence_badge_html(conf), unsafe_allow_html=True)

    with col3:
        clv = customer_row[13] or 0
        st.markdown(f"**CLV:** {format_idr(clv)}")
        dormant = customer_row[11] or 0
        st.caption(f"Dormant: {dormant} days")

    st.divider()
    st.markdown("#### Identity Sources")

    emails = customer_row[1] or []
    phones = customer_row[2] or []
    source_ids = customer_row[8] or []
    systems = customer_row[9] or []

    if emails:
        for i, e in enumerate(emails):
            phone = phones[i] if i < len(phones) else ""
            sid = source_ids[i] if i < len(source_ids) else ""
            sys_name = systems[i] if i < len(systems) else ""
            st.markdown(
                f"- **{e}** | {format_phone(phone) if phone else '—'} | `{sid}` | _{sys_name}_"
            )

    if mcl_row:
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Bookings", mcl_row[3] or 0)
        c2.metric("Completed", mcl_row[4] or 0)
        c3.metric("Cancelled", mcl_row[5] or 0)
        c4.metric("Support Tickets", "Yes" if mcl_row[11] else "No")
