
import pandas as pd
import sqlite3
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "raw"

# Load the CSV datasets
leads = pd.read_csv(DATA_DIR / "leads.csv")
calls = pd.read_csv(DATA_DIR / "calls.csv")

# Create an in-memory SQL database
conn = sqlite3.connect(":memory:")

leads.to_sql("leads", conn, index=False, if_exists="replace")
calls.to_sql("calls", conn, index=False, if_exists="replace")

query = """
SELECT
    l.campaign,
    COUNT(DISTINCT l.lead_id) AS total_leads,
    COUNT(DISTINCT c.call_id) AS total_calls,
    COUNT(DISTINCT CASE
        WHEN c.status = 'connected' THEN c.call_id
    END) AS connected_calls,
    COUNT(DISTINCT CASE
        WHEN c.outcome = 'converted' THEN c.lead_id
    END) AS converted_customers,
    ROUND(
        100.0 * COUNT(DISTINCT CASE
            WHEN c.status = 'connected' THEN c.call_id
        END) / NULLIF(COUNT(DISTINCT c.call_id), 0),
        2
    ) AS connection_rate_pct,
    ROUND(
        100.0 * COUNT(DISTINCT CASE
            WHEN c.outcome = 'converted' THEN c.lead_id
        END) / NULLIF(COUNT(DISTINCT l.lead_id), 0),
        2
    ) AS lead_conversion_rate_pct
FROM leads l
LEFT JOIN calls c
    ON l.lead_id = c.lead_id
GROUP BY l.campaign
ORDER BY l.campaign;
"""

result = pd.read_sql_query(query, conn)

print("\n===== CAMPAIGN PERFORMANCE REPORT =====\n")
print(result.to_string(index=False))

output_file = PROJECT_DIR / "data" / "processed" / "campaign_report.csv"
output_file.parent.mkdir(parents=True, exist_ok=True)
result.to_csv(output_file, index=False)

print(f"\nReport saved to: {output_file}")

conn.close()
