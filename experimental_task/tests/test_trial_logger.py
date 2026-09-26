import csv
import tempfile
import unittest
from pathlib import Path

from core.trial_logger import TRIALS_HEADER, TrialLogger


class TrialLoggerTests(unittest.TestCase):
    def test_mapping_is_written_in_header_order(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "trials.csv"
            logger = TrialLogger(path)
            logger.log_trial(
                {
                    "participant": "P001",
                    "block": 1,
                    "trial": 1,
                    "condition": "A1V1_A2_short",
                    "response": "2",
                }
            )
            logger.close()

            with path.open(newline="", encoding="utf-8") as file_obj:
                rows = list(csv.DictReader(file_obj))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["participant"], "P001")
            self.assertEqual(rows[0]["response"], "2")
            self.assertEqual(list(rows[0]), TRIALS_HEADER)

    def test_trial_schema_is_unchanged(self):
        expected = [
            "participant", "block", "trial", "condition", "base_condition",
            "soa_type", "soa_ms", "position", "response", "rt",
            "correct_answer", "accuracy", "illusion", "illusion_type",
            "fission_illusion", "fusion_illusion", "confidence",
            "confidence_mode", "rt_conf", "fixation_programmed_s",
            "fixation_measured_s", "flash_frames", "isi_frames",
            "flash1_onset_time", "flash1_offset_time",
            "isi_blank_start_time", "isi_blank_end_time",
            "flash2_onset_time", "flash2_offset_time",
            "beep1_scheduled_ptb_time", "beep1_flip_proxy_time",
            "beep2_scheduled_ptb_time", "beep2_flip_proxy_time",
            "soa_visual_programmed_s", "soa_visual_flip_measured_s",
            "soa_audio_programmed_s", "soa_audio_scheduled_s",
            "soa_audio_flip_proxy_s", "isi_blank_programmed_s",
            "isi_blank_measured_s", "dropped_fixation", "dropped_stim1",
            "dropped_isi", "dropped_stim2", "dropped_poststim",
            "dropped_frames_total", "trial_total_s", "error",
        ]
        self.assertEqual(TRIALS_HEADER, expected)

    def test_unknown_mapping_field_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = TrialLogger(Path(temp_dir) / "trials.csv")
            with self.assertRaises(ValueError):
                logger.log_trial({"participant": "P001", "unknown": 1})
            logger.close()


if __name__ == "__main__":
    unittest.main()
