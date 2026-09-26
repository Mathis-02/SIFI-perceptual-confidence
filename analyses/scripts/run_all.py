from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

SCRIPT_ORDER = [
    "00_privacy_audit.py",
    "00_check_data.py",
    "01_prepare_data.py",
    "02_perceptual_descriptives.py",
    "03_confidence_descriptives.py",
    "04_statistical_models.py",
    "05_quality_control.py",
]


def main() -> None:
    for script in SCRIPT_ORDER:
        path = SCRIPTS_DIR / script
        print(f"\n=== Running {script} ===")
        subprocess.run([sys.executable, str(path)], check=True, cwd=PROJECT_ROOT)
    print("\nPipeline completed.")


if __name__ == "__main__":
    main()
