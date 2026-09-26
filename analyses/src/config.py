from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
TRIALS_DIR = DATA_DIR / "trials"
PROCESSED_DIR = DATA_DIR / "processed"

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
TABLES_DIR = OUTPUTS_DIR / "tables"
REPORTS_DIR = OUTPUTS_DIR / "reports"

PERCEPTUAL_FIGURES_DIR = FIGURES_DIR / "perceptual"
CONFIDENCE_FIGURES_DIR = FIGURES_DIR / "confidence"
DIAGNOSTIC_FIGURES_DIR = FIGURES_DIR / "diagnostics"

DESCRIPTIVE_TABLES_DIR = TABLES_DIR / "descriptive"
MODEL_TABLES_DIR = TABLES_DIR / "models"

RAW_TRIALS_PATTERN = "*_trials.csv"

# Conditions attendues dans le design multisensoriel.
FISSION_CONDITION = "A1V1_A2"
FUSION_CONDITION = "A1V1_V2"
CONGRUENT_ONE_CONDITION = "A1V1"
CONGRUENT_TWO_CONDITION = "A1V1_A2V2"

KNOWN_BASE_CONDITIONS = {
    CONGRUENT_ONE_CONDITION,
    FISSION_CONDITION,
    FUSION_CONDITION,
    CONGRUENT_TWO_CONDITION,
}

SOA_NONE_LABEL = "none"

# Colonnes minimales réellement nécessaires pour les premières analyses.
REQUIRED_COLUMNS_MINIMAL = {
    "condition",
    "response",
    "confidence",
}
