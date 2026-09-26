from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import PROCESSED_DIR, DESCRIPTIVE_TABLES_DIR, PERCEPTUAL_FIGURES_DIR
from src.io_utils import ensure_directories, save_csv
from src.summaries import (
    summarize_response2,
    summarize_response2_group,
    summarize_illusion_rates,
    summarize_illusion_group,
)
from src.plotting import plot_response2_rates, plot_illusion_rates


def main() -> None:
    ensure_directories()
    model_path = PROCESSED_DIR / "model_ready_trials.csv"
    if not model_path.exists():
        raise FileNotFoundError("Run scripts/01_prepare_data.py first.")

    df = pd.read_csv(model_path)

    response2_participant = summarize_response2(df)
    response2_group = summarize_response2_group(response2_participant)
    illusion_participant = summarize_illusion_rates(df)
    illusion_group = summarize_illusion_group(illusion_participant)

    save_csv(response2_participant, DESCRIPTIVE_TABLES_DIR / "response2_by_participant_condition_soa.csv")
    save_csv(response2_group, DESCRIPTIVE_TABLES_DIR / "response2_group_condition_soa.csv")
    save_csv(illusion_participant, DESCRIPTIVE_TABLES_DIR / "illusion_rates_by_participant_type_soa.csv")
    save_csv(illusion_group, DESCRIPTIVE_TABLES_DIR / "illusion_rates_group_type_soa.csv")

    plot_response2_rates(response2_participant, PERCEPTUAL_FIGURES_DIR / "01_response2_rate_by_condition_soa.pdf")
    plot_illusion_rates(illusion_participant, PERCEPTUAL_FIGURES_DIR / "02_illusion_rate_fission_fusion_by_soa.pdf")

    print("Perceptual descriptive tables and figures saved.")


if __name__ == "__main__":
    main()
