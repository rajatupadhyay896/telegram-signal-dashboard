import asyncio
from telethon import TelegramClient
import psycopg2
import os
import re
from datetime import datetime, timedelta, timezone

# ===== TELEGRAM CONFIG =====
api_id = 37198242
api_hash = "2e7589b8f971f0f7de6fcd5d84fba979"

groups = [
    "nifty_banknifty_zero_to_hero1",
    "zero_hero_calls_sensex_index",
    "tradingadda11",
    "equity_trader_india",
    "Nifty_and_banknifty_intraday_5"
]

client = TelegramClient("session", api_id, api_hash)

# ===== DB CONNECTION =====
DB_URL = os.getenv("DB_URL")

if not DB_URL:
    raise Exception("DB_URL not set")

conn = psycopg2.connect(DB_URL)
cursor = conn.cursor()

# ===== EXTRACT STRIKE + CE/PE =====
def extract_trade_info(text):
    text = text.upper()

    strike = None
    option_type = None

    match = re.search(r'(\d{4,5})\s*(CE|PE)', text)
    if match:
        strike = int(match.group(1))
        option_type = match.group(2)
    else:
        match = re.search(r'(CE|PE)\s*(\d{4,5})', text)
        if match:
            option_type = match.group(1)
            strike = int(match.group(2))

    return strike, option_type

# ===== FLAGS =====
def detect_flags(text):
    text = text.upper()

    return {
        "has_target": ("TARGET" in text or "TGT" in text),
        "has_sl": ("SL" in text or "STOPLOSS" in text or "STOP LOSS" in text),
        "is_buy": ("BUY" in text),
        "is_sell": ("SELL" in text)
    }

# ===== INSERT FUNCTION =====
def insert_signal(row):
    cursor.execute("""
        INSERT INTO signals (
            timestamp, group_name, message_text, user_id,
            strike, option_type, has_target, has_sl, is_buy, is_sell
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING
    """, (
        row["timestamp"],
        row["group_name"],
        row["message_text"],
        row["user_id"],
        row["strike"],
        row["option_type"],
        row["has_target"],
        row["has_sl"],
        row["is_buy"],
        row["is_sell"]
    ))

# ===== MAIN SCRAPER =====
async def scrape():
    await client.start()

    # FIXED: timezone-aware cutoff
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)

    for group in groups:
        print("Scraping:", group)

        try:
            entity = await client.get_entity(group)

            async for message in client.iter_messages(entity, limit=200):

                if not message.text:
                    continue

                # FIXED: now both timezone-aware
                if message.date < cutoff:
                    break

                strike, option_type = extract_trade_info(message.text)

                if option_type is None:
                    continue

                flags = detect_flags(message.text)

                row = {
                    "timestamp": message.date,  # KEEP timezone-aware
                    "group_name": group,
                    "message_text": message.text,
                    "user_id": str(message.sender_id) if message.sender_id else None,
                    "strike": strike,
                    "option_type": option_type,
                    **flags
                }

                insert_signal(row)

                await asyncio.sleep(0.2)

        except Exception as e:
            print("Error:", group, e)

    conn.commit()
    print("DB UPDATED")

# ===== RUN =====
with client:
    client.loop.run_until_complete(scrape())