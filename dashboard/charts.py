"""
Plotly chart builders. Each function takes a small, already-aggregated
DataFrame (from analytics.py) and returns a go.Figure/px figure — no
aggregation logic lives here, only presentation.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Shared visual language
ACCENT = "#4F8CFF"
ACCENT_2 = "#22C3A6"
NAVY = "#111827"
PALETTE = ["#4F8CFF", "#22C3A6", "#F6B93B", "#EF6C6C", "#9B8CFF", "#4FD1C5", "#F2A65A", "#7EC8E3"]

BASE_LAYOUT = dict(
    font=dict(family="Inter, -apple-system, Segoe UI, Roboto, sans-serif", size=13, color="#1F2937"),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=40, b=10),
    hoverlabel=dict(bgcolor="white", font_size=12),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
)


def _style(fig: go.Figure, title: str | None = None) -> go.Figure:
    fig.update_layout(**BASE_LAYOUT)
    if title:
        fig.update_layout(title=dict(text=title, font=dict(size=15, color=NAVY)))
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)", zeroline=False)
    return fig


def horizontal_bar(df: pd.DataFrame, x: str, y: str, title: str, color: str = ACCENT) -> go.Figure:
    df = df.sort_values(x)
    fig = px.bar(df, x=x, y=y, orientation="h", color_discrete_sequence=[color])
    fig.update_traces(marker_line_width=0)
    return _style(fig, title)


def vertical_bar(df: pd.DataFrame, x: str, y: str, title: str, color: str = ACCENT) -> go.Figure:
    fig = px.bar(df, x=x, y=y, color_discrete_sequence=[color])
    fig.update_traces(marker_line_width=0)
    return _style(fig, title)


def grouped_bar(df: pd.DataFrame, x: str, y: str, color: str, title: str) -> go.Figure:
    fig = px.bar(df, x=x, y=y, color=color, barmode="group", color_discrete_sequence=PALETTE)
    fig.update_traces(marker_line_width=0)
    return _style(fig, title)


def histogram(series: pd.Series, title: str, nbins: int = 40) -> go.Figure:
    fig = px.histogram(series, nbins=nbins, color_discrete_sequence=[ACCENT])
    fig.update_layout(showlegend=False)
    return _style(fig, title)


def box_plot(df: pd.DataFrame, x: str, y: str, title: str) -> go.Figure:
    fig = px.box(df, x=x, y=y, color_discrete_sequence=[ACCENT_2])
    return _style(fig, title)


def scatter(df: pd.DataFrame, x: str, y: str, title: str, hover_data: list[str] | None = None) -> go.Figure:
    fig = px.scatter(df, x=x, y=y, opacity=0.55, color_discrete_sequence=[ACCENT], hover_data=hover_data)
    return _style(fig, title)


def line_chart(df: pd.DataFrame, x: str, y: str, title: str, color: str | None = None) -> go.Figure:
    fig = px.line(df, x=x, y=y, color=color, markers=True, color_discrete_sequence=PALETTE)
    return _style(fig, title)


def pie(df: pd.DataFrame, names: str, values: str, title: str) -> go.Figure:
    fig = px.pie(df, names=names, values=values, hole=0.5, color_discrete_sequence=PALETTE)
    fig.update_traces(textinfo="percent+label")
    return _style(fig, title)
