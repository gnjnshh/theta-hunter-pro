import pandas as pd
from nselib import capital_market, derivatives
from datetime import datetime, timedelta

def get_last_working_day(offset=0):
    dt = datetime.now() - timedelta(days=offset)
    # If today is weekend, go back to Friday
    if dt.weekday() == 5: # Sat
        dt = dt - timedelta(days=1)
    elif dt.weekday() == 6: # Sun
        dt = dt - timedelta(days=2)
    return dt.strftime('%d-%m-%Y')

def get_top_500_active_stocks():
    """
    Fetch the Top 500 stocks by Value (Turnover) from the latest available Bhavcopy.
    """
    # Try last 5 days to find a working Bhavcopy (handling holidays)
    for i in range(5):
        date_str = get_last_working_day(i)
        try:
            data = capital_market.bhav_copy_equities(trade_date=date_str)
            if isinstance(data, pd.DataFrame) and not data.empty:
                sym_col = 'TckrSymb' if 'TckrSymb' in data.columns else 'SYMBOL'
                series_col = 'SctySrs' if 'SctySrs' in data.columns else 'SERIES'
                val_col = 'TtlTrfVal' if 'TtlTrfVal' in data.columns else 'TURNOVER'
                
                if sym_col in data.columns and series_col in data.columns:
                    eq_data = data[data[series_col] == 'EQ']
                    if val_col in eq_data.columns:
                        eq_data[val_col] = pd.to_numeric(eq_data[val_col], errors='coerce')
                        top_500 = eq_data.sort_values(by=val_col, ascending=False).head(500)
                        print(f"Success: Found {len(top_500)} stocks from Bhavcopy dated {date_str}")
                        return top_500[sym_col].tolist()
        except:
            continue
    
    print("Warning: Could not fetch Bhavcopy from last 5 days. Using fallback list.")
    return ['RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'INFY', 'BHARTIARTL', 'SBIN', 'LICI', 'ITC', 'HINDUNILVR']

def get_top_20_active_stocks():
    # Keep this for backward compatibility or simple scans
    return get_top_500_active_stocks()[:20]

def get_fno_ban_list():
    """
    Get the list of stocks in F&O ban period.
    """
    date_str = get_last_working_day()
    try:
        ban_list = derivatives.fno_security_in_ban_period(trade_date=date_str)
        if isinstance(ban_list, pd.DataFrame) and not ban_list.empty:
            return ban_list['SYMBOL'].tolist()
        return []
    except Exception as e:
        print(f"Error fetching F&O ban list: {e}")
        return []

def get_ohlc_history(symbol, days=60):
    """
    Fetch OHLC history for a symbol for the last 'days' days.
    """
    end_date = datetime.now().strftime('%d-%m-%Y')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%d-%m-%Y')
    try:
        # This function name is relatively stable
        data = capital_market.price_volume_and_deliverable_position_data(symbol=symbol, from_date=start_date, to_date=end_date)
        return data
    except Exception as e:
        print(f"Error fetching OHLC for {symbol}: {e}")
        return pd.DataFrame()

def get_fii_sentiment():
    """
    Fetch Participant Wise Open Interest and return FII data.
    """
    date_str = get_last_working_day()
    try:
        data = derivatives.participant_wise_open_interest(trade_date=date_str)
        # Filter for FII row
        if isinstance(data, pd.DataFrame) and 'Client Type' in data.columns:
            fii_data = data[data['Client Type'] == 'FII'].iloc[0]
            return fii_data
        return None
    except Exception as e:
        print(f"Error fetching FII sentiment: {e}")
        return None
