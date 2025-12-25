"""
Notifier module for Discord and Telegram notifications.
Sends Top 10 Sideways Opportunities (Confidence >= 60, sorted by Volume).
"""
import os
import json
import pandas as pd
import urllib.request
import urllib.parse
import urllib.error

def get_top_opportunities():
    """Load market scan and filter for top opportunities."""
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    csv_path = os.path.join(data_dir, 'market_scan.csv')
    
    if not os.path.exists(csv_path):
        print("No market_scan.csv found. Skipping notifications.")
        return None
    
    df = pd.read_csv(csv_path)
    
    # Filter: Passed stocks with Confidence >= 60
    if 'Passed' not in df.columns or 'Confidence' not in df.columns:
        print("Required columns missing. Skipping notifications.")
        return None
    
    filtered = df[(df['Passed'] == True) & (df['Confidence'] >= 60)]
    
    if filtered.empty:
        print("No opportunities meeting criteria. Skipping notifications.")
        return None
    
    # Sort by Volume and get top 10
    if 'Volume' in filtered.columns:
        filtered = filtered.sort_values(by='Volume', ascending=False)
    
    return filtered.head(10)

def format_message(df):
    """Format the opportunities into a readable message."""
    lines = ["🎯 **Theta Hunter Pro - Daily Scan Results**\n"]
    lines.append("```")
    lines.append(f"{'Symbol':<12} {'Close':>8} {'Conf':>6} {'Volume':>12}")
    lines.append("-" * 42)
    
    for _, row in df.iterrows():
        symbol = row.get('Symbol', 'N/A')[:12]
        close = f"{row.get('Close', 0):.2f}"
        conf = f"{row.get('Confidence', 0):.0f}%"
        vol = f"{int(row.get('Volume', 0)):,}"
        lines.append(f"{symbol:<12} {close:>8} {conf:>6} {vol:>12}")
    
    lines.append("```")
    lines.append(f"\n📊 Top {len(df)} Sideways Opportunities | Confidence ≥ 60%")
    return "\n".join(lines)

def send_discord(message):
    """Send message to Discord via webhook."""
    webhook_url = os.environ.get('DISCORD_WEBHOOK')
    if not webhook_url:
        print("DISCORD_WEBHOOK not set. Skipping Discord notification.")
        return False
    
    payload = json.dumps({"content": message}).encode('utf-8')
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'ThetaHunterBot/1.0'
    }
    req = urllib.request.Request(webhook_url, data=payload, headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"Discord notification sent. Status: {response.status}")
            return True
    except urllib.error.HTTPError as e:
        print(f"Discord notification failed: HTTP Error {e.code}: {e.reason}")
        print(f"Response: {e.read().decode('utf-8', errors='ignore')}")
        return False
    except Exception as e:
        print(f"Discord notification failed: {e}")
        return False

def send_telegram(message):
    """Send message to Telegram via Bot API."""
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set. Skipping Telegram notification.")
        return False
    
    # Convert markdown to Telegram-compatible format
    telegram_message = message.replace("**", "*")
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = urllib.parse.urlencode({
        'chat_id': chat_id,
        'text': telegram_message,
        'parse_mode': 'Markdown'
    }).encode('utf-8')
    
    try:
        with urllib.request.urlopen(url, data=params) as response:
            print(f"Telegram notification sent. Status: {response.status}")
            return True
    except Exception as e:
        print(f"Telegram notification failed: {e}")
        return False

def run_notifier():
    """Main function to send notifications."""
    print("Starting notification process...")
    
    top_opps = get_top_opportunities()
    if top_opps is None:
        return
    
    message = format_message(top_opps)
    print(f"Sending notifications for {len(top_opps)} opportunities...")
    
    send_discord(message)
    send_telegram(message)
    
    print("Notification process complete.")

if __name__ == "__main__":
    run_notifier()
