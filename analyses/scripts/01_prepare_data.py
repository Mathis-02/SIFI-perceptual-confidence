from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import PROCESSED_DIR
from src.io_utils import ensure_directories, load_all_trials, save_csv
from src.preprocessing import prepare_trials


def main() -> None:
    ensure_directories()
    raw = load_all_trials()
    clean = prepare_trials(raw)

    save_csv(raw, PROCESSED_DIR / "all_trials_raw_concat.csv")
    save_csv(clean, PROCESSED_DIR / "model_ready_trials.csv")

    print(f"Raw concatenated data saved to: {PROCESSED_DIR / 'all_trials_raw_concat.csv'}")
    print(f"Model-ready data saved to: {PROCESSED_DIR / 'model_ready_trials.csv'}")
    print(f"Rows: {len(clean)} | Participants: {clean['participant'].nunique()}")


if __name__ == "__main__":
    main()
