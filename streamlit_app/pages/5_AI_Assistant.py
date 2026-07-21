import streamlit as st
from labels import LABELS
from components.ai_slots import chat_assistant_slot

L = LABELS["en"]

st.title(f"🤖 {L['ai_assistant']} — Phase 6")

st.info(
    "Natural-language querying, anomaly explanation, and proactive recommendations "
    "are coming in Phase 6. The LangChain agent will answer questions by converting "
    "natural language to ClickHouse SQL using the gold layer marts."
)

st.markdown("### Example queries (Phase 6):")
st.markdown("""
- *"Who are my top 5 customers by CLV and what do they book most?"*
- *"Why did CLV drop in Bali last month?"*
- *"Which customers are at highest churn risk and why?"*
- *"Show me route performance during Lebaran vs normal months."*
""")

chat_placeholder = chat_assistant_slot()
with chat_placeholder:
    st.text_input("Ask anything about your customers...", disabled=True, placeholder="Coming in Phase 6")
