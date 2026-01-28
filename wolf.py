#!/usr/bin/env python3
import requests
import time
import re
import logging
import json
import os
from datetime import datetime
from urllib.parse import urlencode

# ================= CONFIG =================

AJAX_URL = "http://213.32.24.208/ints/client/res/data_smscdr.php"

BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN"
CHAT_ID = os.getenv("CHAT_ID") or "-100XXXXXXXXXX"

COOKIES = {
    "PHPSESSID": os.getenv("PHPSESSID") or "PUT_SESSION_HERE"  # Update this if needed
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "http://213.32.24.208/ints/client/smscdr.php",
    "Connection": "keep-alive"
}

CHECK_INTERVAL = 10  # seconds
STATE_FILE = "state.json"

SUPPORT_URL = "https://t.me/botcasx"
NUMBERS_URL = "https://t.me/CyberOTPCore"

# =========================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

session = requests.Session()
session.headers.update(HEADERS)
session.cookies.update(COOKIES)

# ================= STATE =================

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading state: {e}")
    return {"last_uid": None, "processed_ids": []}

def save_state(state):
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
    except Exception as e:
        logging.error(f"Error saving state: {e}")

STATE = load_state()

# ================= HELPERS =================

def extract_otp(text):
    """Extract OTP from SMS text"""
    if not text:
        return "N/A"
    
    # Try to find Telegram codes
    telegram_match = re.search(r'Telegram code\s+(\d{4,8})', text)
    if telegram_match:
        return telegram_match.group(1)
    
    # General OTP patterns
    patterns = [
        r'\b(\d{4,8})\b',  # 4-8 digit standalone numbers
        r'code[\s:]+(\d{4,8})',
        r'OTP[\s:]+(\d{4,8})',
        r'verification[\s:]+(\d{4,8})',
        r'密码[\s:]+(\d{4,8})',  # Chinese
        r'코드[\s:]+(\d{4,8})',  # Korean
        r'код[\s:]+(\d{4,8})',  # Russian
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return "N/A"

def clean_phone_number(number):
    """Clean and format phone number"""
    if not number:
        return "N/A"
    
    # Remove any non-digit characters
    cleaned = re.sub(r'\D', '', number)
    
    # Add + if it's a valid international number
    if len(cleaned) >= 10:
        return f"+{cleaned}"
    return number

def build_payload():
    """Build the AJAX payload for the new website"""
    today = datetime.now().strftime("%Y-%m-%d")
    timestamp = int(time.time() * 1000)  # Current timestamp for _ parameter
    
    # Base parameters from the provided URL
    params = {
        "fdate1": f"{today} 00:00:00",
        "fdate2": f"{today} 23:59:59",
        "frange": "",
        "fnum": "",
        "fcli": "",
        "fgdate": "",
        "fgmonth": "",
        "fgrange": "",
        "fgnumber": "",
        "fgcli": "",
        "fg": 0,
        "sEcho": 1,
        "iColumns": 7,
        "sColumns": ",,,,,,",  # 6 commas for 7 columns
        "iDisplayStart": 0,
        "iDisplayLength": 25,
        "mDataProp_0": 0,
        "sSearch_0": "",
        "bRegex_0": "false",
        "bSearchable_0": "true",
        "bSortable_0": "true",
        "mDataProp_1": 1,
        "sSearch_1": "",
        "bRegex_1": "false",
        "bSearchable_1": "true",
        "bSortable_1": "true",
        "mDataProp_2": 2,
        "sSearch_2": "",
        "bRegex_2": "false",
        "bSearchable_2": "true",
        "bSortable_2": "true",
        "mDataProp_3": 3,
        "sSearch_3": "",
        "bRegex_3": "false",
        "bSearchable_3": "true",
        "bSortable_3": "true",
        "mDataProp_4": 4,
        "sSearch_4": "",
        "bRegex_4": "false",
        "bSearchable_4": "true",
        "bSortable_4": "true",
        "mDataProp_5": 5,
        "sSearch_5": "",
        "bRegex_5": "false",
        "bSearchable_5": "true",
        "bSortable_5": "true",
        "mDataProp_6": 6,
        "sSearch_6": "",
        "bRegex_6": "false",
        "bSearchable_6": "true",
        "bSortable_6": "true",
        "sSearch": "",
        "bRegex": "false",
        "iSortCol_0": 0,
        "sSortDir_0": "desc",
        "iSortingCols": 1,
        "_": timestamp
    }
    
    return params

def format_message(row):
    """Format the SMS data into a Telegram message"""
    try:
        date = row[0] if len(row) > 0 else "N/A"
        route = row[1] if len(row) > 1 else "Unknown"
        number = clean_phone_number(row[2]) if len(row) > 2 else "N/A"
        service = row[3] if len(row) > 3 else "Unknown"
        message = row[4] if len(row) > 4 else ""
        
        # Extract country from route
        country = "Unknown"
        if route and isinstance(route, str):
            # Split by space and take first part as country
            country = route.split()[0] if route.split() else "Unknown"
        
        # Extract OTP
        otp = extract_otp(message)
        
        # Format the message
        formatted = (
            "📩 *LIVE OTP RECEIVED*\n\n"
            f"📞 *Number:* `{number}`\n"
            f"🔢 *OTP:* 🔥 `{otp}` 🔥\n"
            f"🏷 *Service:* {service}\n"
            f"🌍 *Country:* {country}\n"
            f"🕒 *Time:* {date}\n\n"
            f"💬 *SMS Text:*\n```\n{message}\n```\n\n"
            "⚡ *CYBER CORE OTP*"
        )
        
        return formatted
    except Exception as e:
        logging.error(f"Error formatting message: {e}")
        return None

def send_telegram(text):
    """Send message to Telegram"""
    if not text:
        return
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
        "reply_markup": {
            "inline_keyboard": [
                [
                    {"text": "🆘 Support", "url": SUPPORT_URL},
                    {"text": "📲 Numbers", "url": NUMBERS_URL}
                ]
            ]
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            logging.info("Message sent to Telegram successfully")
        else:
            logging.error(f"Telegram API error: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Error sending to Telegram: {e}")

# ================= CORE LOGIC =================

def fetch_latest_sms():
    """Fetch latest SMS from the new website"""
    global STATE
    
    try:
        # Build payload
        params = build_payload()
        
        # Make request
        logging.info(f"Fetching data from {AJAX_URL}")
        response = session.get(AJAX_URL, params=params, timeout=30)
        
        if response.status_code != 200:
            logging.error(f"HTTP Error: {response.status_code}")
            return
        
        # Parse JSON response
        try:
            data = response.json()
        except json.JSONDecodeError:
            logging.error("Invalid JSON response")
            return
        
        # Extract data rows
        rows = data.get("aaData", [])
        if not rows:
            logging.info("No data found")
            return
        
        # Filter out invalid rows and the summary row
        valid_rows = []
        for row in rows:
            # Skip if row is not a list or too short
            if not isinstance(row, list) or len(row) < 5:
                continue
            
            # Skip summary row (the one that starts with "0,0,0,")
            if isinstance(row[0], str) and row[0].startswith("0,0,0,"):
                continue
            
            # Skip if date is not valid
            if not row[0] or not re.match(r'\d{4}-\d{2}-\d{2}', str(row[0])):
                continue
            
            valid_rows.append(row)
        
        if not valid_rows:
            logging.info("No valid SMS rows found")
            return
        
        # Sort by date (newest first)
        valid_rows.sort(
            key=lambda x: datetime.strptime(x[0], "%Y-%m-%d %H:%M:%S"),
            reverse=True
        )
        
        # Process only the newest row
        newest = valid_rows[0]
        
        # Create unique ID for this SMS
        sms_id = f"{newest[0]}_{newest[2]}_{newest[4][:50]}" if len(newest) > 4 else f"{newest[0]}_{newest[2]}"
        
        # Check if we've already processed this SMS
        if STATE["last_uid"] == sms_id or sms_id in STATE.get("processed_ids", []):
            return
        
        # Format and send message
        formatted_msg = format_message(newest)
        if formatted_msg:
            send_telegram(formatted_msg)
            logging.info(f"New OTP sent for number: {newest[2]}")
        
        # Update state
        STATE["last_uid"] = sms_id
        
        # Keep track of processed IDs (limit to last 100 to prevent memory issues)
        processed_ids = STATE.get("processed_ids", [])
        processed_ids.append(sms_id)
        if len(processed_ids) > 100:
            processed_ids = processed_ids[-100:]
        STATE["processed_ids"] = processed_ids
        
        save_state(STATE)
        
    except requests.RequestException as e:
        logging.error(f"Network error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

# ================= MAIN LOOP =================

def main():
    logging.info("🚀 INTS SMS BOT STARTED (New Website)")
    logging.info(f"Monitoring URL: {AJAX_URL}")
    logging.info(f"Check interval: {CHECK_INTERVAL} seconds")
    
    # Initial test fetch
    try:
        fetch_latest_sms()
    except Exception as e:
        logging.error(f"Initial fetch error: {e}")
    
    # Main loop
    while True:
        try:
            fetch_latest_sms()
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
