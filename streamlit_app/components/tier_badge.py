import streamlit as st
from format import tier_badge_html

def render_tier_badge(tier):
    st.markdown(tier_badge_html(tier), unsafe_allow_html=True)
