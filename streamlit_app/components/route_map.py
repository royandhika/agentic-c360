import plotly.graph_objects as go
import pandas as pd
import os

def _load_cities():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "id_cities.csv")
    return pd.read_csv(path)

def render(city_revenue_df: pd.DataFrame):
    """Plot Indonesia map with city bubbles sized by revenue."""
    cities = _load_cities()

    merged = city_revenue_df.merge(cities, on="city", how="inner")
    if len(merged) == 0:
        return go.Figure()

    max_rev = merged["total_revenue"].max()
    merged["scaled_size"] = (merged["total_revenue"] / max_rev * 40 + 8).clip(upper=50)

    fig = go.Figure()

    fig.add_trace(go.Scattermapbox(
        lat=merged["lat"],
        lon=merged["lng"],
        mode="markers+text",
        marker=dict(
            size=merged["scaled_size"],
            color=merged["total_revenue"],
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(title="Revenue (IDR)"),
            sizemode="diameter",
        ),
        text=merged["city"],
        textposition="top center",
        hovertext=[
            f"<b>{r['city']}</b><br>{r['booking_count']} bookings<br>Revenue: Rp {r['total_revenue']:,.0f}"
            for _, r in merged.iterrows()
        ],
        hoverinfo="text",
    ))

    center_lat = -2.5
    center_lon = 118.0

    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=3.8,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=450,
        template="plotly_dark",
    )
    return fig
