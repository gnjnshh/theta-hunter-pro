import pandas as pd
try:
    import pandas_ta as ta
except ImportError:
    try:
        import pandas_ta_classic as ta
    except ImportError:
        raise ImportError("Neither pandas_ta nor pandas_ta_classic could be imported")
import numpy as np
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
try:
    from nse_fetcher import get_top_500_active_stocks, get_fno_ban_list, get_ohlc_history, get_fii_sentiment
except ImportError:
    from logic.nse_fetcher import get_top_500_active_stocks, get_fno_ban_list, get_ohlc_history, get_fii_sentiment

def calculate_hv(df, window=20):
    if df.empty: return 0
    col = 'ClosePrice' if 'ClosePrice' in df.columns else 'close' if 'close' in df.columns else None
    if not col:
        col = 'ClsgPric' if 'ClsgPric' in df.columns else None
        if not col: return 0

    df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=[col])
    if len(df) < window: return 0
    
    log_returns = np.log(df[col] / df[col].shift(1))
    std_dev = log_returns.rolling(window=window).std()
    hv = std_dev * np.sqrt(252) * 100
    if hv.empty or pd.isna(hv.iloc[-1]):
        return 0
    return hv.iloc[-1]

def analyze_stock(symbol):
    """Worker function to analyze a single stock."""
    try:
        df = get_ohlc_history(symbol)
        if df.empty or len(df) < 30:
            return None
        
        # Clean column names even more aggressively
        df.columns = [c.replace('ï»¿', '').replace(' ', '').strip() for c in df.columns]
        
        close_col = next((c for c in df.columns if 'ClosePrice' in c or 'ClsgPric' in c or 'Close' in c), None)
        high_col = next((c for c in df.columns if 'HighPrice' in c or 'HghPric' in c or 'High' in c), None)
        low_col = next((c for c in df.columns if 'LowPrice' in c or 'LwPric' in c or 'Low' in c), None)
        # Volume could be 'TotalTradedQuantity', 'Volume', 'TradedQty', etc.
        vol_col = next((c for c in df.columns if 'TradedQuantity' in c or 'TradedVolume' in c or 'TradedQty' in c or 'Volume' in c), None)
        
        if not all([close_col, high_col, low_col]):
            return None

        # TA calculations
        try:
            adx_df = ta.adx(pd.to_numeric(df[high_col]), pd.to_numeric(df[low_col]), pd.to_numeric(df[close_col]), length=14)
            adx = adx_df['ADX_14'].iloc[-1]
        except: adx = 99
        
        try:
            rsi = ta.rsi(pd.to_numeric(df[close_col]), length=14).iloc[-1]
        except: rsi = 0
            
        hv = calculate_hv(df)
        last_close = pd.to_numeric(df[close_col]).iloc[-1]
        
        # Robust volume extraction
        last_vol = 0
        if vol_col:
            try:
                last_vol = pd.to_numeric(df[vol_col]).dropna().iloc[-1]
            except: last_vol = 0
        
        # Scoring Logic (0-100)
        # Trend Score: Lower ADX is better for sideways (100 = ADX 0, 0 = ADX 50+)
        trend_score = max(0, min(100, (50 - adx) * 2)) if adx < 50 else 0
        
        # Stability Score: RSI closer to 50 is better (100 = RSI 50, 0 = RSI <30 or >70)
        stability_score = max(0, min(100, 100 - abs(50 - rsi) * 5))
        
        # Volatility Score: Higher HV is better for premiums (100 = HV 60+, 0 = HV 0)
        volatility_score = max(0, min(100, hv * 1.66))
        
        is_sideways = adx < 25
        is_stable = 40 < rsi < 60
        confidence = round((trend_score * 0.4 + stability_score * 0.4 + volatility_score * 0.2), 2)
        passed = is_sideways and is_stable

        return {
            'Symbol': symbol,
            'Close': last_close,
            'Volume': int(last_vol),
            'ADX': round(adx, 2),
            'RSI': round(rsi, 2),
            'HV': round(hv, 2),
            'Trend_Score': round(trend_score, 2),
            'Stability_Score': round(stability_score, 2),
            'Vol_Score': round(volatility_score, 2),
            'Status': "Sideways" if is_sideways else "Trending",
            'Stability': "Stable" if is_stable else "Volatile",
            'Confidence': confidence,
            'StopLoss_L': round(last_close * 0.95, 2),
            'StopLoss_H': round(last_close * 1.05, 2),
            'Target_Put': round(last_close * 0.92, 2),
            'Target_Call': round(last_close * 1.08, 2),
            'Passed': passed
        }
    except Exception as e:
        # print(f"Error analyzing {symbol}: {e}")
        return None

def save_results(results, fii_stats):
    df_results = pd.DataFrame(results)
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    df_results.to_csv(os.path.join(data_dir, 'market_scan.csv'), index=False)
    with open(os.path.join(data_dir, 'fii_stats.json'), 'w') as f:
        json.dump(fii_stats, f)

def run_screener():
    print("Starting Optimized Market Scan (Top 200 Stocks)...")
    
    top_stocks = get_top_500_active_stocks()[:200]  # Focus on top 200 for reliable execution
    ban_list = get_fno_ban_list()
    universe = [s for s in top_stocks if s not in ban_list]
    print(f"Universe size: {len(universe)} stocks. Using conservative parallelization...")

    # Initial FII Sentiment
    fii_data = get_fii_sentiment()
    fii_stats = {"ratio": 1.0, "status": "Neutral"}
    if fii_data is not None:
        try:
            longs = float(fii_data['Future Index Long'])
            shorts = float(fii_data['Future Index Short'])
            ratio = longs / shorts if shorts != 0 else 0
            fii_stats = {"ratio": round(ratio, 2), "status": "Balanced" if 0.8 < ratio < 1.5 else "Risk On", "longs": longs, "shorts": shorts}
        except: pass

    results = []
    with ThreadPoolExecutor(max_workers=3) as executor:  # Reduced for cloud reliability
        futures = {executor.submit(analyze_stock, s): s for s in universe}
        
        count = 0
        for future in as_completed(futures):
            count += 1
            res = future.result()
            if res:
                results.append(res)
            
            # Save every 50 stocks for live updates in dashboard
            if count % 50 == 0:
                print(f"[{count}/{len(universe)}] Stocks processed. Saving partial results...")
                save_results(results, fii_stats)

    # Final Save
    save_results(results, fii_stats)
    print(f"Scan complete. {len(results)} stocks saved to market_scan.csv.")

if __name__ == "__main__":
    run_screener()
