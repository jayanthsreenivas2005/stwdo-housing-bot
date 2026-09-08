import os
import json
import requests
from bs4 import BeautifulSoup

# URL of STWDO Dortmund Housing
URL = "https://www.stwdo.de/wohnen/aktuelle-wohnangebote"
SEEN_FILE = "seen_ads.json"

# Telegram Secrets (Loaded securely from environment variables)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def load_seen_ads():
    """Load previously detected ad identifiers."""
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen_ads(seen_ads):
    """Save updated ad identifiers."""
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen_ads), f)

def send_telegram_alert(message):
    """Send alert directly to your phone via Telegram."""
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(telegram_url, data=payload)
    except Exception as e:
        print(f"Error sending Telegram notification: {e}")

def check_for_new_ads():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch website: {e}")
        return

    soup = BeautifulSoup(response.content, "html.parser")
    
    # Locate all listing elements on the page
    ads = soup.select(".wohnangebot-item") or soup.find_all("article") or soup.select(".offer-item")
    
    current_ads = {}
    
    for ad in ads:
        text_content = ad.get_text(" ", strip=True)
        if text_content:
            # Create a unique identifier for each listing
            ad_id = str(hash(text_content))
            current_ads[ad_id] = text_content[:150] # First 150 characters

    seen_ads = load_seen_ads()
    new_ads_found = []

    for ad_id, ad_text in current_ads.items():
        if ad_id not in seen_ads:
            new_ads_found.append(ad_text)
            seen_ads.add(ad_id)

    if new_ads_found:
        print(f"Found {len(new_ads_found)} new listing(s)!")
        alert_msg = f"🚨 *NEW HOUSING OFFER ON STWDO!*\n\n"
        for idx, text in enumerate(new_ads_found, 1):
            alert_msg += f"{idx}. {text}...\n\n"
        alert_msg += f"👉 [Click to Apply Immediately]({URL})"
        
        send_telegram_alert(alert_msg)
        save_seen_ads(seen_ads)
    else:
        print("No new listings found.")

if __name__ == "__main__":
    check_for_new_ads()
