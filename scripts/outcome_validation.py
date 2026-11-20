
import pandas as pd
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_DIR / "data" / "raw" / "calls.csv"
OUTPUT_DIR = PROJECT_DIR / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

calls = pd.read_csv(DATA_FILE)


def validate_outcome(row):
    transcript = str(row["transcript"]).lower().strip()
    outcome = str(row["outcome"]).lower().strip()
    status = str(row["status"]).lower().strip()

    negative_keywords = [
        "not interested",
        "declined",
        "rejected",
        "do not want",
        "don't want"
    ]

    positive_keywords = [
        "interested in the loan",
        "wants to know more",
        "would like to proceed",
        "agreed to proceed",
        "ready to apply"
    ]

    conversion_keywords = [
        "loan approved",
        "successfully converted",
        "completed the application",
        "agreed to take the loan"
    ]

    # 1. Handle failed calls first
    if status == "failed":
        if outcome == "failed":
            return pd.Series([
                "OK",
                "Call failed; transcript validation not required"
            ])
        return pd.Series([
            "MISMATCH",
            "Call failed but outcome is not recorded as failed"
        ])

    # 2. Missing transcript in a connected call
    if pd.isna(row["transcript"]) or not transcript:
        return pd.Series([
            "REVIEW",
            "Connected call has missing transcript"
        ])

    # 3. Check negative statements first
    has_negative = any(word in transcript for word in negative_keywords)
    has_positive = any(word in transcript for word in positive_keywords)
    has_conversion = any(word in transcript for word in conversion_keywords)

    if outcome == "interested":
        if has_negative:
            return pd.Series([
                "MISMATCH",
                "Recorded interested but transcript suggests rejection"
            ])
        if has_positive:
            return pd.Series(["OK", "Interest supported by transcript"])
        return pd.Series([
            "REVIEW",
            "Transcript does not clearly confirm interest"
        ])

    elif outcome == "not_interested":
        if has_positive or has_conversion:
            return pd.Series([
                "MISMATCH",
                "Recorded not interested but transcript suggests interest/conversion"
            ])
        if has_negative:
            return pd.Series(["OK", "Rejection supported by transcript"])
        return pd.Series([
            "REVIEW",
            "Transcript does not clearly confirm rejection"
        ])

    elif outcome == "converted":
        if has_negative:
            return pd.Series([
                "MISMATCH",
                "Recorded converted but transcript suggests rejection"
            ])
        if has_conversion:
            return pd.Series(["OK", "Conversion supported by transcript"])
        return pd.Series([
            "REVIEW",
            "Transcript does not clearly confirm conversion"
        ])

    return pd.Series(["REVIEW", "Unknown outcome category"])


# Apply validation
calls[["validation_status", "validation_reason"]] = calls.apply(
    validate_outcome,
    axis=1
)

# Generate summary
print("\n===== CALL OUTCOME VALIDATION REPORT =====\n")

print(
    calls[
        ["call_id", "status", "outcome",
         "validation_status", "validation_reason"]
    ].to_string(index=False)
)

print("\n===== VALIDATION SUMMARY =====")

print("Total calls:", len(calls))
print("\nStatus counts:")
print(calls["validation_status"].value_counts())

# Save detailed report
output_file = OUTPUT_DIR / "outcome_validation_report.csv"
calls.to_csv(output_file, index=False)

print(f"\nReport saved to: {output_file}")
print("\nValidation complete!")
