# =============================================================================
# PORTFOLIO RISK DASHBOARD
# A complete quant analytics project for your internship portfolio
# =============================================================================

import pandas as pd
import numpy as np
from scipy import stats
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# SECTION 1: PORTFOLIO DEFINITION
# =============================================================================

PORTFOLIO = {
    "AAPL":  {"shares": 50,  "asset_class": "Equity",   "sector": "Technology"},
    "MSFT":  {"shares": 30,  "asset_class": "Equity",   "sector": "Technology"},
    "JPM":   {"shares": 40,  "asset_class": "Equity",   "sector": "Finance"},
    "XOM":   {"shares": 60,  "asset_class": "Equity",   "sector": "Energy"},
    "JNJ":   {"shares": 25,  "asset_class": "Equity",   "sector": "Healthcare"},
    "TLT":   {"shares": 100, "asset_class": "Bond ETF", "sector": "Fixed Income"},
    "GLD":   {"shares": 20,  "asset_class": "Commodity","sector": "Gold"},
}

STRESS_SCENARIOS = {
    "2008 Financial Crisis": {
        "Equity":       -0.45,
        "Bond ETF":     +0.15,
        "Commodity":    -0.30,
    },
    "COVID Crash (Mar 2020)": {
        "Equity":       -0.35,
        "Bond ETF":     +0.08,
        "Commodity":    -0.10,
    },
    "Rate Shock +200bps": {
        "Equity":       -0.15,
        "Bond ETF":     -0.18,
        "Commodity":    +0.05,
    },
}

# =============================================================================
# SECTION 2: DATA FETCHING
# =============================================================================

def fetch_data(tickers: list, period: str = "2y") -> pd.DataFrame:
    """Download historical closing prices from Yahoo Finance."""
    raw = yf.download(tickers, period=period, auto_adjust=True, progress=False)
    prices = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw
    prices = prices.dropna()
    return prices


def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Convert prices to daily log returns."""
    return np.log(prices / prices.shift(1)).dropna()


# =============================================================================
# SECTION 3: PORTFOLIO METRICS
# =============================================================================

def get_current_prices(prices: pd.DataFrame) -> dict:
    """Get the most recent price for each ticker."""
    return prices.iloc[-1].to_dict()


def compute_portfolio_value(prices: dict) -> dict:
    """Calculate market value and weights for each position."""
    positions = {}
    total = 0.0

    for ticker, meta in PORTFOLIO.items():
        price = prices.get(ticker, 0)
        value = price * meta["shares"]
        positions[ticker] = {
            "shares":       meta["shares"],
            "price":        round(price, 2),
            "value":        round(value, 2),
            "asset_class":  meta["asset_class"],
            "sector":       meta["sector"],
        }
        total += value

    for ticker in positions:
        positions[ticker]["weight"] = round(positions[ticker]["value"] / total * 100, 2)

    return positions, round(total, 2)


def compute_var(returns: pd.DataFrame, positions: dict, total_value: float,
                confidence: float = 0.95) -> dict:
    """
    Compute Value at Risk using three methods:
    1. Historical Simulation  — sort actual past returns
    2. Parametric             — assume normal distribution
    3. Monte Carlo            — simulate 10,000 random scenarios
    """
    weights = np.array([positions[t]["weight"] / 100 for t in returns.columns
                        if t in positions])
    port_returns = returns[[t for t in returns.columns if t in positions]] @ weights

    # --- Method 1: Historical ---
    var_hist = float(np.percentile(port_returns, (1 - confidence) * 100))

    # --- Method 2: Parametric ---
    mu    = port_returns.mean()
    sigma = port_returns.std()
    var_param = float(stats.norm.ppf(1 - confidence, mu, sigma))

    # --- Method 3: Monte Carlo ---
    np.random.seed(42)
    sim = np.random.normal(mu, sigma, 10_000)
    var_mc = float(np.percentile(sim, (1 - confidence) * 100))

    # CVaR = average loss beyond VaR (also called Expected Shortfall)
    cvar = float(port_returns[port_returns <= var_hist].mean())

    return {
        "historical":  round(var_hist  * total_value, 2),
        "parametric":  round(var_param * total_value, 2),
        "monte_carlo": round(var_mc    * total_value, 2),
        "cvar":        round(cvar      * total_value, 2),
        "port_returns": port_returns,
        "var_hist_pct": round(var_hist * 100, 4),
    }


def compute_leverage(positions: dict, total_value: float) -> dict:
    """
    Gross leverage = sum of absolute position values / NAV
    For a long-only portfolio this is always 1.0.
    Net leverage   = (longs - shorts) / NAV
    """
    long_value  = sum(p["value"] for p in positions.values())
    short_value = 0  # long-only portfolio
    gross_lev = round(long_value / total_value, 4)
    net_lev   = round((long_value - short_value) / total_value, 4)
    return {"gross": gross_lev, "net": net_lev}


def compute_exposure(positions: dict) -> dict:
    """Break down portfolio exposure by asset class and sector."""
    by_class  = {}
    by_sector = {}
    for ticker, p in positions.items():
        by_class[p["asset_class"]]  = by_class.get(p["asset_class"], 0)  + p["value"]
        by_sector[p["sector"]]      = by_sector.get(p["sector"], 0)       + p["value"]
    return {"by_class": by_class, "by_sector": by_sector}


def run_stress_tests(positions: dict, total_value: float) -> dict:
    """Apply each stress scenario to the portfolio and compute P&L."""
    results = {}
    for name, shocks in STRESS_SCENARIOS.items():
        pnl = 0.0
        for ticker, p in positions.items():
            shock = shocks.get(p["asset_class"], 0)
            pnl += p["value"] * shock
        results[name] = {
            "pnl":     round(pnl, 2),
            "pnl_pct": round(pnl / total_value * 100, 2),
        }
    return results


# =============================================================================
# SECTION 4: CHARTS
# =============================================================================

COLORS = {
    "primary":   "#1a1a2e",
    "accent":    "#e94560",
    "teal":      "#0f3460",
    "gold":      "#f5a623",
    "green":     "#27ae60",
    "red":       "#e74c3c",
    "bg":        "#16213e",
    "card":      "#0f3460",
    "text":      "#eaeaea",
    "muted":     "#8892b0",
}

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor ="rgba(0,0,0,0)",
    font=dict(color=COLORS["text"], family="IBM Plex Mono"),
    margin=dict(l=40, r=20, t=30, b=40),
)


def chart_var_distribution(var_data: dict, confidence: float) -> go.Figure:
    port_returns = var_data["port_returns"] * 100
    var_line     = var_data["var_hist_pct"]

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=port_returns, nbinsx=80,
        marker_color=COLORS["teal"], opacity=0.8,
        name="Daily returns",
    ))
    # Shade the tail (losses beyond VaR)
    tail = port_returns[port_returns <= var_line]
    fig.add_trace(go.Histogram(
        x=tail, nbinsx=30,
        marker_color=COLORS["accent"], opacity=0.9,
        name=f"Loss tail ({int(confidence*100)}% VaR)",
    ))
    fig.add_vline(x=var_line, line_color=COLORS["gold"],
                  line_dash="dash", line_width=2,
                  annotation_text=f"VaR {var_line:.2f}%",
                  annotation_font_color=COLORS["gold"])
    fig.update_layout(**CHART_LAYOUT, title="Return distribution & VaR",
                      barmode="overlay", showlegend=True,
                      legend=dict(bgcolor="rgba(0,0,0,0)"))
    return fig


def chart_exposure_pie(exposure: dict) -> go.Figure:
    fig = make_subplots(rows=1, cols=2,
                        specs=[[{"type":"pie"}, {"type":"pie"}]])
    ac = exposure["by_class"]
    fig.add_trace(go.Pie(
        labels=list(ac.keys()), values=list(ac.values()),
        name="Asset class", hole=0.45,
        marker_colors=[COLORS["teal"], COLORS["gold"], COLORS["accent"]],
        textfont_color=COLORS["text"],
    ), row=1, col=1)

    sec = exposure["by_sector"]
    fig.add_trace(go.Pie(
        labels=list(sec.keys()), values=list(sec.values()),
        name="Sector", hole=0.45,
        textfont_color=COLORS["text"],
    ), row=1, col=2)

    fig.update_layout(**CHART_LAYOUT,
                      title="Exposure: asset class (left) · sector (right)",
                      showlegend=False)
    return fig


def chart_stress(stress_results: dict, total_value: float) -> go.Figure:
    names  = list(stress_results.keys())
    pnls   = [stress_results[n]["pnl"]     for n in names]
    colors = [COLORS["red"] if p < 0 else COLORS["green"] for p in pnls]

    fig = go.Figure(go.Bar(
        x=names, y=pnls, marker_color=colors,
        text=[f"${p:,.0f}" for p in pnls],
        textposition="outside", textfont_color=COLORS["text"],
    ))
    fig.update_layout(**CHART_LAYOUT, title="Stress test P&L ($)",
                      yaxis_title="P&L ($)")
    return fig


def chart_cumulative_returns(returns: pd.DataFrame, positions: dict) -> go.Figure:
    tickers = [t for t in returns.columns if t in positions]
    weights = np.array([positions[t]["weight"] / 100 for t in tickers])
    port_r  = (returns[tickers] @ weights)
    cum_r   = (1 + port_r).cumprod() - 1

    fig = go.Figure()
    for t in tickers:
        cum_t = (1 + returns[t]).cumprod() - 1
        fig.add_trace(go.Scatter(
            x=cum_t.index, y=cum_t * 100,
            name=t, mode="lines", opacity=0.5,
            line=dict(width=1),
        ))
    fig.add_trace(go.Scatter(
        x=cum_r.index, y=cum_r * 100,
        name="Portfolio", mode="lines",
        line=dict(color=COLORS["gold"], width=3),
    ))
    fig.update_layout(**CHART_LAYOUT, title="Cumulative returns (%)",
                      yaxis_title="%", showlegend=True,
                      legend=dict(bgcolor="rgba(0,0,0,0)"))
    return fig


# =============================================================================
# SECTION 5: DASH APP LAYOUT
# =============================================================================

def build_app(prices, returns, positions, total_value,
              var_data, leverage, exposure, stress):

    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

    def kpi_card(title, value, sub="", color="#eaeaea"):
        return dbc.Card(dbc.CardBody([
            html.P(title, style={"fontSize": "11px", "color": "#8892b0",
                                 "marginBottom": "4px", "textTransform": "uppercase",
                                 "letterSpacing": "1px"}),
            html.H4(value, style={"color": color, "fontFamily": "IBM Plex Mono",
                                  "marginBottom": "2px"}),
            html.Small(sub, style={"color": "#8892b0", "fontSize": "11px"}),
        ]), style={"background": "#0f3460", "border": "1px solid #1a1a2e",
                   "borderRadius": "8px"})

    var_h = var_data["historical"]
    var_p = var_data["parametric"]
    var_m = var_data["monte_carlo"]
    cvar  = var_data["cvar"]

    # ---- positions table ----
    tbl_data = [
        {"Ticker": t,
         "Shares": p["shares"],
         "Price": f'${p["price"]:,.2f}',
         "Value": f'${p["value"]:,.0f}',
         "Weight": f'{p["weight"]}%',
         "Asset Class": p["asset_class"],
         "Sector": p["sector"]}
        for t, p in positions.items()
    ]

    app.layout = dbc.Container([
        # ── Header ──────────────────────────────────────────────────
        dbc.Row(dbc.Col(html.Div([
            html.H2("PORTFOLIO RISK DASHBOARD",
                    style={"fontFamily": "IBM Plex Mono", "color": "#e94560",
                           "letterSpacing": "3px", "marginBottom": "4px"}),
            html.P(f"NAV: ${total_value:,.2f}  ·  {len(positions)} positions  ·  "
                   f"Updated: {datetime.now().strftime('%Y-%m-%d')}",
                   style={"color": "#8892b0", "fontFamily": "IBM Plex Mono",
                          "fontSize": "13px"}),
        ])), style={"padding": "24px 0 12px"}),

        # ── KPI row ─────────────────────────────────────────────────
        dbc.Row([
            dbc.Col(kpi_card("Total NAV",        f"${total_value:,.0f}"), width=2),
            dbc.Col(kpi_card("Gross Leverage",   f"{leverage['gross']:.2f}x"), width=2),
            dbc.Col(kpi_card("VaR 95% (Hist.)",  f"${abs(var_h):,.0f}",
                             "1-day loss", "#e94560"), width=2),
            dbc.Col(kpi_card("VaR 95% (Param.)", f"${abs(var_p):,.0f}",
                             "1-day loss", "#e94560"), width=2),
            dbc.Col(kpi_card("VaR 95% (MC)",     f"${abs(var_m):,.0f}",
                             "1-day loss", "#e94560"), width=2),
            dbc.Col(kpi_card("CVaR 95%",          f"${abs(cvar):,.0f}",
                             "Expected Shortfall", "#f5a623"), width=2),
        ], className="g-2", style={"marginBottom": "16px"}),

        # ── Charts row 1 ─────────────────────────────────────────────
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody(
                dcc.Graph(figure=chart_var_distribution(var_data, 0.95),
                          config={"displayModeBar": False})
            ), style={"background": "#0f3460", "border": "1px solid #1a1a2e",
                      "borderRadius": "8px"}), width=6),
            dbc.Col(dbc.Card(dbc.CardBody(
                dcc.Graph(figure=chart_cumulative_returns(returns, positions),
                          config={"displayModeBar": False})
            ), style={"background": "#0f3460", "border": "1px solid #1a1a2e",
                      "borderRadius": "8px"}), width=6),
        ], className="g-2", style={"marginBottom": "16px"}),

        # ── Charts row 2 ─────────────────────────────────────────────
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody(
                dcc.Graph(figure=chart_exposure_pie(exposure),
                          config={"displayModeBar": False})
            ), style={"background": "#0f3460", "border": "1px solid #1a1a2e",
                      "borderRadius": "8px"}), width=6),
            dbc.Col(dbc.Card(dbc.CardBody(
                dcc.Graph(figure=chart_stress(stress, total_value),
                          config={"displayModeBar": False})
            ), style={"background": "#0f3460", "border": "1px solid #1a1a2e",
                      "borderRadius": "8px"}), width=6),
        ], className="g-2", style={"marginBottom": "16px"}),

        # ── Positions table ──────────────────────────────────────────
        dbc.Row(dbc.Col(dbc.Card(dbc.CardBody([
            html.P("POSITIONS", style={"fontSize": "11px", "color": "#8892b0",
                                       "letterSpacing": "2px", "marginBottom": "8px"}),
            dash_table.DataTable(
                data=tbl_data,
                columns=[{"name": c, "id": c} for c in tbl_data[0].keys()],
                style_table={"overflowX": "auto"},
                style_header={"backgroundColor": "#1a1a2e", "color": "#e94560",
                              "fontFamily": "IBM Plex Mono", "fontSize": "11px",
                              "border": "none"},
                style_cell={"backgroundColor": "#0f3460", "color": "#eaeaea",
                            "fontFamily": "IBM Plex Mono", "fontSize": "12px",
                            "border": "1px solid #1a1a2e", "padding": "8px"},
                style_data_conditional=[{
                    "if": {"row_index": "odd"},
                    "backgroundColor": "#16213e",
                }],
            ),
        ]), style={"background": "#0f3460", "border": "1px solid #1a1a2e",
                   "borderRadius": "8px"})), style={"marginBottom": "32px"}),

    ], fluid=True, style={"background": "#16213e", "minHeight": "100vh",
                          "padding": "0 24px"})

    return app


# =============================================================================
# SECTION 6: MAIN — wire everything together and launch
# =============================================================================

if __name__ == "__main__":
    print("Fetching market data...")
    tickers = list(PORTFOLIO.keys())
    prices  = fetch_data(tickers, period="2y")
    returns = compute_returns(prices)

    print("Computing portfolio metrics...")
    current_prices        = get_current_prices(prices)
    positions, total_value = compute_portfolio_value(current_prices)
    var_data               = compute_var(returns, positions, total_value, confidence=0.95)
    leverage               = compute_leverage(positions, total_value)
    exposure               = compute_exposure(positions)
    stress                 = run_stress_tests(positions, total_value)

    print(f"\nPortfolio NAV:    ${total_value:,.2f}")
    print(f"VaR 95% (Hist.):  ${abs(var_data['historical']):,.2f}")
    print(f"Gross Leverage:   {leverage['gross']:.2f}x")
    print("\nLaunching dashboard at http://127.0.0.1:8050 ...")

    app = build_app(prices, returns, positions, total_value,
                    var_data, leverage, exposure, stress)
    app.run(debug=False)
