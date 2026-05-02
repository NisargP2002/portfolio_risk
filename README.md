# 📊 Portfolio Risk Dashboard

A full-stack quantitative finance analytics dashboard built with Python and Dash, designed to analyze portfolio risk, exposure, and stress scenarios in real time.

---

## 🚀 Overview

This project simulates a multi-asset investment portfolio and provides advanced risk analytics including:

- 📉 Value at Risk (VaR)
- 📊 Conditional VaR (Expected Shortfall)
- 📈 Portfolio returns & performance
- ⚖️ Leverage calculations
- 🧠 Stress testing (financial crises scenarios)
- 🧩 Asset class & sector exposure
- 📋 Interactive dashboard for visualization

The dashboard is built using Dash + Plotly, making it interactive and production-ready.

---

## 🏗️ Features

### 📌 Portfolio Composition
- Multi-asset portfolio (Equities, Bonds, Commodities)
- Sector classification (Technology, Finance, Energy, etc.)
- Position weights and allocation

---

### 📉 Risk Metrics

#### Value at Risk (VaR)
Implemented using 3 methods:
- Historical Simulation
- Parametric (Gaussian assumption)
- Monte Carlo Simulation (10,000 scenarios)

#### CVaR (Expected Shortfall)
- Measures average loss beyond VaR threshold

---

### ⚖️ Leverage Analysis
- Gross leverage
- Net leverage (long-only portfolio)

---

### 🧪 Stress Testing
Simulated real-world shocks:
- 2008 Financial Crisis
- COVID-19 Market Crash (2020)
- Interest Rate Shock (+200bps)

---

### 📊 Visualizations
- Return distribution with VaR threshold
- Cumulative returns comparison
- Portfolio exposure (sector & asset class)
- Stress test P&L impact
- Interactive positions table

---

## 🛠️ Tech Stack

- Python
- Pandas / NumPy – Data processing
- SciPy – Statistical modeling
- yfinance – Market data
- Plotly – Interactive charts
- Dash – Web dashboard
- Dash Bootstrap Components – UI styling

---

## 📂 Project Structure

portfolio-risk-dashboard/
│
├── main.py                # Main application script
├── requirements.txt      # Dependencies
├── README.md             # Project documentation
└── outputs/              # Saved charts (optional)
---

## ▶️ Run the Dashboard

bash python main.py 

Then open:

http://127.0.0.1:8050

---

## 📈 Example Output

The dashboard displays:

- Portfolio NAV
- VaR & CVaR metrics
- Exposure breakdown
- Stress scenario losses
- Real-time charts

---

## 🧠 Key Concepts Demonstrated

- Quantitative risk modeling
- Financial time series analysis
- Monte Carlo simulation
- Portfolio construction & weighting
- Interactive data visualization
- Full-stack Python dashboard development

---

## 🎯 Use Cases

- Quant Finance / Risk Analyst portfolios
- Hedge fund analytics prototypes
- Risk management dashboards
- Financial engineering projects

---

