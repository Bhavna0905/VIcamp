
import pandas as pd
from pathlib import Path

# Find the project directory
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Sample customer leads
leads = pd.DataFrame([
    {"lead_id": 101, "customer_name": "Aarav",
     "campaign": "Loan_A", "city": "Jaipur"},
    {"lead_id": 102, "customer_name": "Priya",
     "campaign": "Loan_A", "city": "Delhi"},
    {"lead_id": 103, "customer_name": "Rahul",
     "campaign": "Loan_B", "city": "Mumbai"},
    {"lead_id": 104, "customer_name": "Neha",
     "campaign": "Loan_B", "city": "Jaipur"},
    {"lead_id": 105, "customer_name": "Kabir",
     "campaign": "Loan_A", "city": "Delhi"},
])

# Sample AI call records
calls = pd.DataFrame([
    {"call_id": 1, "lead_id": 101, "status": "connected",
     "outcome": "interested", "duration_sec": 120,
     "transcript": "Customer is interested in the loan."},
    {"call_id": 2, "lead_id": 102, "status": "connected",
     "outcome": "not_interested", "duration_sec": 80,
     "transcript": "Customer declined the loan offer."},
    {"call_id": 3, "lead_id": 103, "status": "failed",
     "outcome": "failed", "duration_sec": 0,
     "transcript": ""},
    {"call_id": 4, "lead_id": 104, "status": "connected",
     "outcome": "interested", "duration_sec": 150,
     "transcript": "Customer wants to know more about the loan."},
    {"call_id": 5, "lead_id": 105, "status": "connected",
     "outcome": "converted", "duration_sec": 210,
     "transcript": "Customer accepted the offer and completed signup."},
])

# Export the datasets
leads.to_csv(DATA_DIR / "leads.csv", index=False)
calls.to_csv(DATA_DIR / "calls.csv", index=False)

print("Sample datasets created successfully!")
print(f"Leads saved: {len(leads)}")
print(f"Call records saved: {len(calls)}")
print(f"Location: {DATA_DIR}")
