
import sqlite3
import pandas as pd
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent

LEADS_FILE = BASE_DIR / "data" / "raw" / "leads.csv"
CALLS_FILE = BASE_DIR / "data" / "raw" / "calls.csv"
DB_FILE = BASE_DIR / "data" / "processed" / "voice_analytics.db"

DB_FILE.parent.mkdir(parents=True, exist_ok=True)

# Step 1: Read CSV files using Pandas
leads = pd.read_csv(LEADS_FILE)
calls = pd.read_csv(CALLS_FILE)

print("CSV files loaded successfully!")
print("Leads:", len(leads))
print("Calls:", len(calls))

# Step 2: Connect to SQLite
conn = sqlite3.connect(DB_FILE)
conn.execute("PRAGMA foreign_keys = ON")

try:
    with conn:

        # Step 3: Create database tables
        conn.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                lead_id INTEGER PRIMARY KEY,
                customer_name TEXT,
                campaign TEXT,
                city TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS calls (
                call_id INTEGER PRIMARY KEY,
                lead_id INTEGER,
                status TEXT,
                outcome TEXT,
                duration_sec INTEGER,
                transcript TEXT,
                FOREIGN KEY (lead_id)
                REFERENCES leads(lead_id)
            )
        """)

        # Step 4: Clear old data before reloading
        conn.execute("DELETE FROM calls")
        conn.execute("DELETE FROM leads")

        # Step 5: Insert leads into SQLite
        def convert_rows(df):
            return [
                tuple(
                    None if pd.isna(v)
                    else v.item() if hasattr(v, "item")
                    else v
                    for v in row
                )
                for row in df.itertuples(index=False, name=None)
            ]

        conn.executemany(
            """INSERT INTO leads
               (lead_id, customer_name, campaign, city)
               VALUES (?, ?, ?, ?)""",
            convert_rows(leads)
        )

        # Step 6: Insert calls into SQLite
        conn.executemany(
            """INSERT INTO calls
               (call_id, lead_id, status, outcome,
                duration_sec, transcript)
               VALUES (?, ?, ?, ?, ?, ?)""",
            convert_rows(calls)
        )

    # Step 7: Verify database
    lead_count = conn.execute(
        "SELECT COUNT(*) FROM leads"
    ).fetchone()[0]

    call_count = conn.execute(
        "SELECT COUNT(*) FROM calls"
    ).fetchone()[0]

    print("\nDatabase created successfully!")
    print("Leads inserted:", lead_count)
    print("Calls inserted:", call_count)

    print("\nSample joined data:")

    result = pd.read_sql_query("""
        SELECT
            l.customer_name,
            l.campaign,
            c.status,
            c.outcome,
            c.duration_sec
        FROM leads l
        JOIN calls c
        ON l.lead_id = c.lead_id
        LIMIT 5
    """, conn)

    print(result)

except Exception as e:
    print("Database loading failed:", e)

finally:
    conn.close()
