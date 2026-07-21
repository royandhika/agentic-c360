import plotly.graph_objects as go
import pandas as pd

def render(bookings_df: pd.DataFrame):
    if bookings_df is None or len(bookings_df) == 0:
        return go.Figure()

    colors = {"hotel": "#6366f1", "flight": "#22d3ee", "experience": "#f0b429"}
    symbols = {"completed": "circle", "cancelled": "x", "no_show": "triangle-up"}

    fig = go.Figure()

    for btype in bookings_df["booking_type"].unique():
        subset = bookings_df[bookings_df["booking_type"] == btype]
        for status in subset["status"].unique():
            sset = subset[subset["status"] == status]
            sizes = sset["amount_idr"].fillna(100000).clip(lower=100000) / 100000
            fig.add_trace(go.Scatter(
                x=sset["booking_ts"],
                y=sset["amount_idr"],
                mode="markers",
                name=f"{btype} ({status})",
                marker=dict(
                    size=sizes.clip(lower=8, upper=40),
                    color=colors.get(btype, "#8b8fa3"),
                    symbol=symbols.get(status, "circle"),
                    line=dict(width=1, color="white"),
                ),
                text=[
                    f"<b>{r['provider']}</b><br>"
                    f"City: {r['city']}<br>"
                    f"Amount: Rp {r['amount_idr']:,.0f}<br>"
                    f"Payment: {r['payment_method']}<br>"
                    f"Booking: {r['booking_id']}"
                    for _, r in sset.iterrows()
                ],
                hoverinfo="text",
            ))

    fig.update_layout(
        title="Booking Timeline",
        xaxis_title="Booking Date",
        yaxis_title="Amount (IDR)",
        hovermode="closest",
        template="plotly_dark",
        showlegend=True,
    )
    return fig
