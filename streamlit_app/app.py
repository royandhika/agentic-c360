import streamlit as st
import plotly.io as pio

pio.templates.default = "plotly_dark"

st.set_page_config(
    page_title="WanderFuel Customer 360",
    page_icon="🛩️",
    layout="wide",
)

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp {background-color: #0f1117;}
</style>
""", unsafe_allow_html=True)

st.title("WanderFuel Customer 360")
st.markdown("Explore customer insights, CLV, loyalty tiers, and booking history.")
st.markdown("---")
st.markdown("Use the sidebar navigation to explore:")
st.markdown("- **Executive Overview** — KPIs, charts, top customers")
st.markdown("- **Customer Explorer** — Filter and search all customers")
st.markdown("- **Customer 360** — Deep dive on individual customers")
st.markdown("- **Route Analytics** — Route performance and seasonality")
st.markdown("- **AI Assistant** — Natural language queries (Phase 6)")
