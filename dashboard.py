import json
from pathlib import Path
import pandas as pd
from fastapi import FastAPI
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import dash

SIGNAL_LOG_FILE = Path("signals_log.jsonl")

def load_signals():
    if not SIGNAL_LOG_FILE.exists():
        return pd.DataFrame()
    records = []
    with open(SIGNAL_LOG_FILE, "r") as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except:
                continue
    df = pd.DataFrame(records)
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

# ---- FastAPI ----
fastapi_app = FastAPI(title="Signal Dashboard API")

# ---- Dash App ----
dash_app = dash.Dash(
    __name__,
    server=fastapi_app,
    url_base_pathname="/dashboard/"
)

def create_layout():
    df = load_signals()
    if df.empty:
        return html.Div("No signals logged yet.")

    # Equity Curve (Cumulative Score)
    df_sorted = df.sort_values("timestamp")
    df_sorted["cum_score"] = df_sorted["score"].cumsum()

    # Winrate by Session
    session_winrate = df.groupby("session")["score"].apply(lambda x: (x>0).mean()*100).to_dict()

    return html.Div([
        html.H2("📊 Institutional Bot Dashboard"),
        html.Div([
            html.H4("Equity Curve"),
            dcc.Graph(
                figure=go.Figure(
                    data=[go.Scatter(
                        x=df_sorted["timestamp"],
                        y=df_sorted["cum_score"],
                        mode="lines+markers",
                        name="Cumulative Score"
                    )],
                    layout=go.Layout(yaxis_title="Cumulative Score", xaxis_title="Time")
                )
            )
        ]),
        html.Div([
            html.H4("Winrate by Session"),
            dcc.Graph(
                figure=go.Figure(
                    data=[go.Bar(
                        x=list(session_winrate.keys()),
                        y=list(session_winrate.values()),
                        text=[f"{v:.1f}%" for v in session_winrate.values()],
                        textposition="auto"
                    )],
                    layout=go.Layout(yaxis_title="Winrate (%)", xaxis_title="Session")
                )
            )
        ])
    ])

dash_app.layout = create_layout
