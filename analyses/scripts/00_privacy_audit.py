"""Scan public CSV files for obvious direct identifiers and unsafe columns."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
REPORT = ROOT / "outputs" / "reports" / "privacy_audit.txt"

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
UNSAFE_COLUMN_RE = re.compile(
    r"(^|_)(name|firstname|lastname|email|phone|address|birth|consent|contact)($|_)",
    re.I,
)


def main() -> None:
    findings: list[str] = []
    csv_files = sorted(DATA_DIR.rglob("*.csv"))

    for path in csv_files:
        data = pd.read_csv(path, dtype=str, low_memory=False)
        unsafe_columns = [column for column in data.columns if UNSAFE_COLUMN_RE.search(column)]
        if unsafe_columns:
            findings.append(f"{path.relative_to(ROOT)}: unsafe column names {unsafe_columns}")

        for column in data.columns:
            values = data[column].dropna().astype(str)
            if values.str.contains(EMAIL_RE).any():
                findings.append(f"{path.relative_to(ROOT)}: email-like value in {column}")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    status = "PASS" if not findings else "REVIEW REQUIRED"
    lines = [f"Privacy audit status: {status}", f"CSV files scanned: {len(csv_files)}", ""]
    lines.extend(findings or ["No obvious direct identifiers were detected."])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(REPORT)


if __name__ == "__main__":
    main()
