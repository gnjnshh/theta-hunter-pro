# Short Strangle Bot

An automated NSE options screener for identifying "Sideways" stocks for Short Strangle strategies.

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
