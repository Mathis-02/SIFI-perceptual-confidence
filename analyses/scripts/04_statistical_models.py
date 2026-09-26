from __future__ import annotations

"""Export model-ready subsets for inferential modeling in R.

The primary inferential tables are produced by scripts/R/run_models_publication_v2.R.
This Python script only creates transparent CSV subsets for reproducibility and manual checks.
"""

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (  # noqa: E402
    PROCESSED_DIR,
    MODEL_TABLES_DIR,
    FISSION_CONDITION,
    FUSION_CONDITION,
    CONGRUENT_TWO_CONDITION,
    CONGRUENT_ONE_CONDITION,
)
from src.io_utils import ensure_directories, save_csv  # noqa: E402


def add_condition_cell(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["condition_cell"] = out["base_condition"].astype(str)
    has_soa = out["soa_type"].isin(["standard", "short"])
    out.loc[has_soa, "condition_cell"] = (
        out.loc[has_soa, "base_condition"].astype(str)
        + "_"
        + out.loc[has_soa, "soa_type"].astype(str)
    )
    out.loc[out["base_condition"].eq(CONGRUENT_ONE_CONDITION), "condition_cell"] = CONGRUENT_ONE_CONDITION
    return out


def main() -> None:
    ensure_directories()
    df = pd.read_csv(PROCESSED_DIR / "model_ready_trials.csv")
    df = add_condition_cell(df)

    # Perceptual manipulation-check subset: all response2 cells, without assigning
    # a fictive SOA to A1V1.
    perceptual_cells = df[
        df["base_condition"].isin([
            CONGRUENT_ONE_CONDITION,
            FISSION_CONDITION,
            CONGRUENT_TWO_CONDITION,
            FUSION_CONDITION,
        ])
        & df["response2"].notna()
    ].copy()
    save_csv(perceptual_cells, MODEL_TABLES_DIR / "model_subset_response2_condition_cell.csv")

    # Primary perceptual model subset: fission/fusion illusion variable.
    illusion_subset = df[
        df["illusion_type"].isin(["fission", "fusion"])
        & df["soa_type"].isin(["short", "standard"])
        & df["illusion"].notna()
    ].copy()
    save_csv(illusion_subset, MODEL_TABLES_DIR / "model_subset_illusion_type_soa.csv")

    # Primary matched-confidence fission subset: reported 2 flashes.
    fission_matched = df[
        df["base_condition"].isin([FISSION_CONDITION, CONGRUENT_TWO_CONDITION])
        & df["response2"].eq(1)
        & df["soa_type"].isin(["short", "standard"])
        & df["confidence"].notna()
    ].copy()
    save_csv(fission_matched, MODEL_TABLES_DIR / "model_subset_confidence_fission_matched_R2.csv")

    # Primary matched-confidence fusion subset: reported 1 flash.
    fusion_matched = df[
        df["base_condition"].isin([FUSION_CONDITION, CONGRUENT_ONE_CONDITION])
        & df["response2"].eq(0)
        & df["confidence"].notna()
    ].copy()
    save_csv(fusion_matched, MODEL_TABLES_DIR / "model_subset_confidence_fusion_matched_R1.csv")

    print("Model-ready subset CSVs exported to outputs/tables/models/.")
    print("Primary R model/table script: scripts/R/run_models_publication_v2.R")


if __name__ == "__main__":
    main()
