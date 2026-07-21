import streamlit as st
from format import format_idr

def kpi_card(label, value, fmt="number", suffix=""):
    displayed = value
    if fmt == "idr":
        displayed = format_idr(value)
    elif fmt == "pct":
        displayed = f"{value:.1f}%"
    st.metric(label, f"{displayed}{suffix}")

def kpi_row(cards: list[dict], num_cols: int = 5):
    """cards = [{'label': str, 'value': any, 'fmt': str, 'suffix': str}, ...]"""
    cols = st.columns(num_cols)
    for i, card in enumerate(cards):
        with cols[i % num_cols]:
            kpi_card(
                label=card.get("label", ""),
                value=card.get("value", 0),
                fmt=card.get("fmt", "number"),
                suffix=card.get("suffix", ""),
            )
