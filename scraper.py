import asyncio
from telethon import TelegramClient
import pandas as pd
import psycopg2
import re

# ===== TELEGRAM API =====
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

# ===== POSTGRES CONNECTION =====
conn = psycopg2.connect(
    dbname="telegram_trading",
    user="user",
    password="",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# ===== EXTRACTION FUNCTION =====
def extract_trade_info(text):
    text = text.upper()

    strike = None
    option_type = None

    # Match "19500 CE"
    match = re.search(r'(\d{4,5})\s*(CE|PE)', text)
    if match:
        strike = int(match.group(1))
        option_type = match.group(2)
    else:
        # Match "CE 19500"
        match = re.search(r'(CE|PE)\s*(\d{4,5})', text)
        if match:
            option_type = match.group(1)
            strike = int(match.group(2))

    return strike, option_type

# ===== MAIN SCRAPER =====
async def scrape():
    await client.start()

    data = []

    for group in groups:
        print("Scraping:", group)

        try:
            entity = await client.get_entity(group)

            async for message in client.iter_messages(entity, limit=1000):

                if message.text:
                    strike, option_type = extract_trade_info(message.text)

                    data.append({
                        "timestamp": message.date,
                        "group_name": group,
                        "message_text": message.text,
                        "user_id": str(message.sender_id) if message.sender_id else None,
                        "strike": strike,
                        "option_type": option_type
                    })

                await asyncio.sleep(0.2)

        except Exception as e:
            print("Error in group:", group, "|", e)

    df = pd.DataFrame(data)

    if df.empty:
        print("No data scraped")
        return

    # ===== FILTER ONLY VALID SIGNALS =====
    df = df[df["option_type"].notnull()]

    print("Total usable signals:", len(df))

    # ===== SAVE CSV =====
    df.to_csv("signals_only.csv", index=False)
    print("CSV saved as signals_only.csv")

    # ===== INSERT INTO DATABASE =====
    for _, row in df.iterrows():
        cursor.execute("""
        INSERT INTO signals (
            timestamp, group_name, message_text, user_id,
            strike, option_type
        ) VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        """, (
            row["timestamp"],
            row["group_name"],
            row["message_text"],
            row["user_id"],
            row["strike"],
            row["option_type"]
        ))

    conn.commit()

    print("DATA READY FOR ANALYSIS")

# ===== RUN =====
with client:
    client.loop.run_until_complete(scrape())