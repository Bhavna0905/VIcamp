
import pandas as pd
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "raw"

leads = pd.read_csv(DATA_DIR / "leads.csv")
calls = pd.read_csv(DATA_DIR / "calls.csv")

print("===== DATA QUALITY REPORT =====\n")

# 1. Check missing values
print("1. Missing values in leads:")
print(leads.isnull().sum())

print("\nMissing values in calls:")
print(calls.isnull().sum())

# 2. Check duplicate records
print("\n2. Duplicate lead IDs:", leads["lead_id"].duplicated().sum())
print("Duplicate call IDs:", calls["call_id"].duplicated().sum())

# 3. Check calls with no matching lead
unmatched = calls[~calls["lead_id"].isin(leads["lead_id"])]
print("\n3. Calls without a matching lead:", len(unmatched))

# 4. Check invalid call durations
invalid_duration = calls[calls["duration_sec"] < 0]
print("4. Calls with negative duration:", len(invalid_duration))

# 5. Check connected calls with empty transcripts
empty_transcripts = calls[
    (calls["status"] == "connected") &
    (calls["transcript"].fillna("").str.strip() == "")
]
print("5. Connected calls with empty transcripts:", len(empty_transcripts))

print("\n===== CHECK COMPLETE =====")
