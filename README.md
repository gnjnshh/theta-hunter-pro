# 🎯 Theta Hunter Pro
**Delta-Neutral Options Screener for NSE Stocks**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge.svg)](https://theta-hunter-pro.streamlit.app/)
[![Daily Market Scan](https://github.com/gnjnshh/theta-hunter-pro/actions/workflows/daily_scan.yml/badge.svg)](https://github.com/gnjnshh/theta-hunter-pro/actions/workflows/daily_scan.yml)

## 🚀 Live Dashboard
View the latest sideways opportunities here: **[theta-hunter-pro.streamlit.app](https://theta-hunter-pro.streamlit.app/)**

## Features
- **Daily Scan**: Runs automatically via GitHub Actions at market close.
- **Trend Filtering**: Uses ADX and RSI to find non-trending, stable stocks.
- **Volatility Check**: Calculates Historical Volatility (HV) to ensure good premiums.
- **Institutional Sentiment**: Monitors FII Long/Short ratios.
- **Dashboard**: Interactive Streamlit interface to view results and check live 20-Delta strikes.

## Directory Structure
- `.github/workflows/`: Automation instructions.
- `data/`: Resultant CSV and JSON files.
- `logic/`: Core data fetching and screening math.
- `app.py`: Streamlit Dashboard.
- `requirements.txt`: Project dependencies.
