import hashlib
import json
import random
import unittest
from collections import Counter

from config import CONDITION_SPECS_BY_DESIGN
from core.experiment import (
    MAX_CONSECUTIVE_SAME_COND,
    MAX_CONSECUTIVE_SAME_FAMILY,
    MAX_CONSECUTIVE_SAME_POSITION,
    _max_run_by_key,
    generate_blocks,
)


REFERENCE_HASHES = {
    "standard_4cond": "3704c92a223fbf04762e3b72821cc778a31a6ff2fc7ce8e7b3b4e11731ff3a6a",
    "short_soa_6cond": "f8bb1997341b022987dc3931ad25918f3ce4780e8c2c1619588fb585f656e1fe",
    "av_fission_fusion_2soa": "c1a1042cdc255be9ac911d6160512f6d10877443ef86e4441de6752da91fd84b",
}

REFERENCE_FIELDS = [
    "condition_label",
    "base_condition",
    "soa_ms",
    "soa_type",
    "correct_answer",
    "family",
    "position",
]


class ExperimentalDesignTests(unittest.TestCase):
    def test_all_designs_preserve_original_seeded_sequences(self):
        for design_mode, condition_specs in CONDITION_SPECS_BY_DESIGN.items():
            with self.subTest(design_mode=design_mode):
                rng = random.Random(123456)
                blocks = generate_blocks(
                    condition_specs=condition_specs,
                    n_blocks=8,
                    rng=rng,
                )
                projected = [
                    [
                        {field: trial[field] for field in REFERENCE_FIELDS}
                        for trial in block
                    ]
                    for block in blocks
                ]
                payload = json.dumps(
                    projected,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                digest = hashlib.sha256(payload).hexdigest()
                self.assertEqual(digest, REFERENCE_HASHES[design_mode])

    def test_all_designs_generate_576_trials(self):
        for design_mode, condition_specs in CONDITION_SPECS_BY_DESIGN.items():
            with self.subTest(design_mode=design_mode):
                blocks = generate_blocks(
                    condition_specs=condition_specs,
                    n_blocks=8,
                    rng=random.Random(17),
                )
                self.assertEqual(len(blocks), 8)
                self.assertTrue(all(len(block) == 72 for block in blocks))
                self.assertEqual(sum(len(block) for block in blocks), 576)

    def test_condition_counts_and_randomization_constraints(self):
        for design_mode, condition_specs in CONDITION_SPECS_BY_DESIGN.items():
            blocks = generate_blocks(
                condition_specs=condition_specs,
                n_blocks=8,
                rng=random.Random(2026),
            )
            for block in blocks:
                counts = Counter(trial["condition_label"] for trial in block)
                expected = {
                    label: int(spec["n_per_block"])
                    for label, spec in condition_specs.items()
                }
                self.assertEqual(counts, expected, design_mode)
                self.assertLessEqual(
                    _max_run_by_key(block, lambda trial: trial["condition_label"]),
                    MAX_CONSECUTIVE_SAME_COND,
                )
                self.assertLessEqual(
                    _max_run_by_key(block, lambda trial: trial["family"]),
                    MAX_CONSECUTIVE_SAME_FAMILY,
                )
                self.assertLessEqual(
                    _max_run_by_key(block, lambda trial: trial["position"]),
                    MAX_CONSECUTIVE_SAME_POSITION,
                )

            for condition_label in condition_specs:
                positions = Counter(
                    trial["position"]
                    for block in blocks
                    for trial in block
                    if trial["condition_label"] == condition_label
                )
                self.assertEqual(
                    positions["upper"],
                    positions["lower"],
                    f"{design_mode}: {condition_label}",
                )


if __name__ == "__main__":
    unittest.main()
