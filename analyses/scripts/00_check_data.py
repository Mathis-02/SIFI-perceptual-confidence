from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import TRIALS_DIR, REPORTS_DIR, REQUIRED_COLUMNS_MINIMAL
from src.io_utils import ensure_directories, list_trial_files, load_trial_file, check_required_columns, write_text


def main() -> None:
    ensure_directories()
    lines = []
    lines.append("SIFI multisensory participant data - data check")
    lines.append("=" * 45)
    lines.append(f"Trials directory: {TRIALS_DIR}")

    files = list_trial_files(TRIALS_DIR)
    lines.append(f"Number of trial files found: {len(files)}")

    if not files:
        lines.append("\nNo *_trials.csv files found. Place CSV files in data/trials/.")
    for path in files:
        df = load_trial_file(path)
        missing = check_required_columns(df, REQUIRED_COLUMNS_MINIMAL)
        lines.append("\n" + path.name)
        lines.append(f"  shape: {df.shape[0]} rows x {df.shape[1]} columns")
        lines.append(f"  participant(s): {sorted(df['participant'].astype(str).unique().tolist())}")
        lines.append(f"  missing minimal columns: {missing if missing else 'none'}")
        if "condition" in df.columns:
            lines.append("  condition counts:")
            for condition, n in df["condition"].value_counts(dropna=False).items():
                lines.append(f"    {condition}: {n}")
        if "response" in df.columns:
            lines.append("  response counts:")
            for response, n in df["response"].value_counts(dropna=False).items():
                lines.append(f"    {response}: {n}")
        if "confidence" in df.columns:
            c = df["confidence"]
            lines.append(f"  confidence missing: {int(c.isna().sum())}")
            lines.append(f"  confidence min/max: {c.min()} / {c.max()}")

    report_path = REPORTS_DIR / "00_data_check.txt"
    write_text(report_path, "\n".join(lines) + "\n")
    print(f"Data check written to: {report_path}")


if __name__ == "__main__":
    main()
