import pandas as pd
import psycopg2

# LOAD YOUR CSV
df = pd.read_csv("signals_only.csv")

# CONNECT TO NEON
conn = psycopg2.connect("postgresql://neondb_owner:npg_1DWscdB9Pjwu@ep-floral-smoke-ann9y638.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require")
cursor = conn.cursor()

# CREATE TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP,
    group_name TEXT,
    message_text TEXT,
    user_id TEXT,
    strike INTEGER,
    option_type TEXT,
    has_target BOOLEAN,
    has_sl BOOLEAN,
    is_buy BOOLEAN,
    is_sell BOOLEAN
);
""")

# INSERT DATA
for _, row in df.iterrows():
    cursor.execute("""
        INSERT INTO signals (
            timestamp, group_name, message_text, user_id,
            strike, option_type, has_target, has_sl, is_buy, is_sell
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        row.get("timestamp"),
        row.get("group_name"),
        row.get("message_text"),
        row.get("user_id"),
        row.get("strike"),
        row.get("option_type"),
        False,
        False,
        False,
        False
    ))

conn.commit()
cursor.close()
conn.close()

print("Data uploaded to Neon")
