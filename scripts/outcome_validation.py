
import pandas as pd
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_DIR / "data" / "raw" / "calls.csv"
OUTPUT_DIR = PROJECT_DIR / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

calls = pd.read_csv(DATA_FILE)

# Simple keyword-based validation for our sample dataset
def validate_outcome(row):
    transcript = str(row["transcript"]).lower().strip()
    outcome = str(row["outcome"]).lower().strip()

    if not transcript or transcript == "nan":
        return "REVIEW: Missing transcript"

    if outcome == "interested" and any(
        phrase in transcript
        for phrase in ["declined", "not interested", "rejected"]
    ):
        return "MISMATCH: Recorded interested, transcript suggests rejection"

    if outcome == "not_interested" and any(
        phrase in transcript
        for phrase in ["interested in the loan", "wants to know more"]
    ):
        return "MISMATCH: Recorded not interested, transcript suggests interest"

    if outcome == "converted" and any(
        phrase in transcript
        for phrase in ["declined", "not interested", "rejected"]
    ):
        return "MISMATCH: Recorded converted, transcript suggests rejection"

    return "OK"

calls["validation_result"] = calls.apply(validate_outcome, axis=1)

print("\n===== CALL OUTCOME VALIDATION =====\n")
print(
    calls[["call_id", "outcome", "validation_result"]].to_string(index=False)
)

output_file = OUTPUT_DIR / "outcome_validation_report.csv"
calls.to_csv(output_file, index=False)

print(f"\nReport saved to: {output_file}")
print("\nValidation complete!")
