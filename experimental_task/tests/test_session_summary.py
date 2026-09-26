import csv
import tempfile
import unittest
from pathlib import Path

from core.session_summary import build_session_summary, format_session_summary
from core.trial_logger import TRIALS_HEADER


class SessionSummaryTests(unittest.TestCase):
    def test_fission_and_fusion_definitions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "trials.csv"
            rows = [
                self._row(1, "A1V1_A2_short", "A1V1_A2", "short", 50, "2", 80),
                self._row(1, "A1V1_A2_short", "A1V1_A2", "short", 50, "1", 90),
                self._row(1, "A1V1_V2_short", "A1V1_V2", "short", 50, "1", 70),
                self._row(1, "A1V1_V2_short", "A1V1_V2", "short", 50, "2", 85),
            ]
            with path.open("w", newline="", encoding="utf-8") as file_obj:
                writer = csv.DictWriter(file_obj, fieldnames=TRIALS_HEADER)
                writer.writeheader()
                writer.writerows(rows)

            summary = build_session_summary(path, "av_fission_fusion_2soa")
            by_condition = {
                row["condition"]: row for row in summary.condition_rows
            }

            fission = by_condition["A1V1_A2_short"]
            self.assertEqual(fission["illusion_type"], "fission")
            self.assertEqual(fission["illusion_rate"], 0.5)
            self.assertEqual(fission["mean_confidence_illusion"], 80)
            self.assertEqual(fission["mean_confidence_no_illusion"], 90)

            fusion = by_condition["A1V1_V2_short"]
            self.assertEqual(fusion["illusion_type"], "fusion")
            self.assertEqual(fusion["illusion_rate"], 0.5)
            self.assertEqual(fusion["mean_confidence_illusion"], 70)
            self.assertEqual(fusion["mean_confidence_no_illusion"], 85)

    def test_console_summary_includes_display_stability(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "trials.csv"
            rows = [
                self._row(1, "A1V1_A2_short", "A1V1_A2", "short", 50, "2", 80),
                self._row(1, "A1V1_A2_short", "A1V1_A2", "short", 50, "1", 90),
            ]
            with path.open("w", newline="", encoding="utf-8") as file_obj:
                writer = csv.DictWriter(file_obj, fieldnames=TRIALS_HEADER)
                writer.writeheader()
                writer.writerows(rows)

            summary = build_session_summary(path, "av_fission_fusion_2soa")
            text = format_session_summary(
                summary,
                {
                    "framerate": 59.98,
                    "frame_median_ms": 16.67,
                    "frame_sd_ms": 0.12,
                },
            )
            self.assertIn("Measured refresh rate: 59.980 Hz", text)
            self.assertIn("Frame duration, median / SD: 16.670 ms / 0.120 ms", text)
            self.assertIn("A1V1_A2_short", text)

    @staticmethod
    def _row(block, condition, base_condition, soa_type, soa_ms, response, confidence):
        row = {field: "" for field in TRIALS_HEADER}
        row.update(
            {
                "participant": "P001",
                "block": block,
                "trial": 1,
                "condition": condition,
                "base_condition": base_condition,
                "soa_type": soa_type,
                "soa_ms": soa_ms,
                "response": response,
                "confidence": confidence,
                "dropped_frames_total": 0,
            }
        )
        return row


if __name__ == "__main__":
    unittest.main()
