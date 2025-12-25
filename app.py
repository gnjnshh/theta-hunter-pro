import streamlit as st
import pandas as pd
import json
import os
import plotly.graph_objects as go

st.set_page_config(page_title="Short Strangle Bot", layout="wide")

# --- Styling ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stTable { background-color: #161b22; }
    .metric-card {
        background-color: #161b22;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #30363d;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Data Loading ---
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
SCAN_FILE = os.path.join(DATA_DIR, 'market_scan.csv')
FII_FILE = os.path.join(DATA_DIR, 'fii_stats.json')

def load_data():
    if os.path.exists(SCAN_FILE):
        df = pd.read_csv(SCAN_FILE)
    else:
        df = pd.DataFrame()
    
    if os.path.exists(FII_FILE):
        with open(FII_FILE, 'r') as f:
            fii = json.load(f)
    else:
        fii = {"ratio": 1.0, "status": "No Data"}
    
    return df, fii

df, fii = load_data()

# --- Header ---
st.title("🎯 Theta Hunter Pro")

# --- Top Picks ---
if not df.empty:
    # Filter for Passing stocks first and sort by Volume
    if 'Volume' in df.columns:
        passing_df = df[df['Passed'] == True].sort_values(by='Volume', ascending=False).reset_index(drop=True)
    else:
        passing_df = df[df['Passed'] == True].sort_values(by='Confidence', ascending=False).reset_index(drop=True)
    
    st.write(f"Showing {len(passing_df)} liquid sideways opportunities out of {len(df)} stocks scanned.")
    
    st.subheader("Top Sideways Opportunities (Sorted by Volume)")
    st.info("👆 Click on a row in the table below to see the Detailed Scoring breakdown.")
    
    # Selection logic for the table
    # We display a subset of columns but keep the scores in the background data
    available_cols = df.columns.tolist()
    target_cols = ['Symbol', 'Status', 'Close', 'Volume', 'Confidence', 'Target_Put', 'Target_Call']
    cols_to_show = [c for c in target_cols if c in available_cols]
    
    display_df = passing_df[cols_to_show]
    # Rename for display
    rename_dict = {
        'Symbol': 'Symbol',
        'Status': 'Trend Status',
        'Close': 'Close',
        'Volume': 'Volume (Qty)',
        'Confidence': 'Total Confidence %',
        'Target_Put': 'Sell Put Strike',
        'Target_Call': 'Sell Call Strike'
    }
    display_df.columns = [rename_dict.get(c, c) for c in display_df.columns]
    
    # Enable selection
    event = st.dataframe(
        display_df.style.background_gradient(subset=['Total Confidence %'], cmap='Greens'),
        height=450, 
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row"
    )
    
    # Handle selection event
    if event and event.selection and event.selection.get("rows"):
        selected_idx = event.selection["rows"][0]
        row = passing_df.iloc[selected_idx]
        
        st.markdown(f"### 📊 Detailed Scores for **{row['Symbol']}**")
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Trend Score", f"{row.get('Trend_Score', 0)}/100")
        with c2: st.metric("Stability Score", f"{row.get('Stability_Score', 0)}/100")
        with c3: st.metric("Volatility Score", f"{row.get('Vol_Score', 0)}/100")
        with c4: st.metric("Total Confidence", f"{row.get('Confidence', 0)}%")
        st.divider()

    st.header("🔍 Full Market Scan Results")
    st.write("Browse all processed stocks. Use the search/filter in the table header to find specifics.")
    # Large height for full scan results
    st.dataframe(df.drop(columns=['Passed'] if 'Passed' in df.columns else []), height=600, use_container_width=True)
else:
    st.info("Scan in progress or no data available. Once the 'Brain' writes the CSV, results will appear here.")

# --- FII Meter ---
st.divider()
st.header("📊 FII Sentiment Meter")

fig = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = fii.get('ratio', 1.0),
    domain = {'x': [0, 1], 'y': [0, 1]},
    title = {'text': f"FII Long/Short Ratio<br><span style='font-size:0.8em;color:gray'>{fii.get('status', 'Neutral')}</span>"},
    gauge = {
        'axis': {'range': [0, 3], 'tickwidth': 1, 'tickcolor': "white"},
        'bar': {'color': "#1f77b4"},
        'bgcolor': "white",
        'borderwidth': 2,
        'bordercolor': "gray",
        'steps': [
            {'range': [0, 0.4], 'color': '#ff4b4b'},
            {'range': [0.4, 0.8], 'color': '#ffa500'},
            {'range': [0.8, 1.5], 'color': '#00cc96'},
            {'range': [1.5, 2.0], 'color': '#ffa500'},
            {'range': [2.0, 3.0], 'color': '#ff4b4b'}
        ],
        'threshold': {
            'line': {'color': "red", 'width': 4},
            'thickness': 0.75,
            'value': 2.5
        }
    }
))

fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white", 'family': "Arial"})
st.plotly_chart(fig, use_container_width=True)

# --- Strategy Logic ---
st.divider()
with st.expander("📚 Understanding the Screening Logic", expanded=True):
    st.markdown("""
    ### The "Edge" of Theta Hunter
    This bot identifies liquid stocks that are likely to stay in a price range (sideways), allowing option sellers to profit from time decay (Theta).
    
    #### 1. Trend Score (ADX Based)
    - **Indicator**: ADX 14.
    - **Score**: 0 to 100. (100 = perfectly sideways, 0 = strong trend). 
    - **Logic**: We target stocks where **Trend Score > 50** (ADX < 25).
    
    #### 2. Stability Score (RSI Based)
    - **Indicator**: RSI 14.
    - **Score**: 0 to 100. (100 = RSI at exactly 50, 0 = RSI <30 or >70).
    - **Logic**: We target stocks where **Stability Score > 50** (RSI between 40-60).
    
    #### 3. Volatility Score (HV Based)
    - **Indicator**: 20-Day Historical Volatility.
    - **Score**: 0 to 100. Higher is better for premiums.
    
    #### 4. Total Confidence %
    A weighted average of the above scores:
    - **Trend (40%)** + **Stability (40%)** + **Volatility (20%)**.
    
    #### 5. Strike Calculation
    - **Sell Put Strike**: Current Close - 8%.
    - **Sell Call Strike**: Current Close + 8%.
    - **Stop Loss**: ± 5% from entry.
    """)

# --- Footer ---
st.markdown("---")
st.caption("Theta Hunter Pro | Built for Automated Alpha | Data updates daily at 3:45 PM IST.")
