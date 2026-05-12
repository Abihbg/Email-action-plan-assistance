"""Simple evaluation helper for the Email Action Plan Assistant.

This script does not automatically judge the LLM. It creates a scoring sheet so the
student or grader can run the app/baseline on each example and score the outputs
using the project rubric.
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_PATH = ROOT / "data" / "eval_examples.json"
OUTPUT_PATH = ROOT / "data" / "manual_scoring_sheet.csv"

RUBRIC_COLUMNS = [
    "structured_completeness_1_5",
    "structured_accuracy_1_5",
    "structured_hallucination_control_1_5",
    "structured_missing_info_handling_1_5",
    "structured_usability_1_5",
    "baseline_completeness_1_5",
    "baseline_accuracy_1_5",
    "baseline_hallucination_control_1_5",
    "baseline_missing_info_handling_1_5",
    "baseline_usability_1_5",
    "notes",
]


def main() -> None:
    examples = json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))
    rows = []
    for ex in examples:
        row = {
            "id": ex["id"],
            "case_type": ex["case_type"],
            "user_request": ex["user_request"],
            "expected_good_output": ex["expected_good_output"],
        }
        for col in RUBRIC_COLUMNS:
            row[col] = ""
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Created scoring sheet: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
