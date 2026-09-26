from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.confidence_figure import plot_confidence_composite_abcd
from src.config import CONFIDENCE_FIGURES_DIR, DESCRIPTIVE_TABLES_DIR, PROCESSED_DIR
from src.io_utils import ensure_directories, save_csv
from src.summaries import summarize_matched_confidence


def main() -> None:
    """Generate the confidence figure included in the submitted thesis."""
    ensure_directories()

    model_path = PROCESSED_DIR / "model_ready_trials.csv"
    if not model_path.exists():
        raise FileNotFoundError(
            "Run scripts/01_prepare_data.py before generating the confidence figure."
        )

    trials = pd.read_csv(model_path)
    matched = summarize_matched_confidence(trials)

    save_csv(
        matched,
        DESCRIPTIVE_TABLES_DIR / "matched_percept_confidence_by_participant.csv",
    )

    plot_confidence_composite_abcd(
        trials,
        matched,
        CONFIDENCE_FIGURES_DIR / "03_confidence_composite_abcd.pdf",
    )

    print("Thesis confidence figure saved.")


if __name__ == "__main__":
    main()
