"""Trial-list construction and constrained randomization."""

import random
from typing import Any, Mapping, Sequence

from config import CONDITION_SPECS, N_BLOCKS
# Maximum number of consecutive trials with the same condition label.
MAX_CONSECUTIVE_SAME_COND = 3
# Maximum number of consecutive trials from the same condition family. 
# Families are defined in config.py and group related conditions more broadly 
# than the exact condition label, such as one-flash and two-flash structures.
MAX_CONSECUTIVE_SAME_FAMILY = 6
# Maximum number of consecutive trials presented at the same visual position.
MAX_CONSECUTIVE_SAME_POSITION = 3
MAX_BUILD_ATTEMPTS = 5000

TrialSpec = dict[str, Any]
ConditionSpecs = Mapping[str, Mapping[str, Any]]


def _max_run_by_key(sequence: Sequence[TrialSpec], key) -> int:
    if not sequence:
        return 0

    max_run = 1
    current_run = 1
    previous_value = key(sequence[0])

    for trial in sequence[1:]:
        current_value = key(trial)
        if current_value == previous_value:
            current_run += 1
            max_run = max(max_run, current_run)
        else:
            current_run = 1
            previous_value = current_value

    return max_run


def _valid_extension(sequence: list[TrialSpec], trial: TrialSpec) -> bool:
    test_sequence = sequence + [trial]
    return (
        _max_run_by_key(test_sequence, lambda item: item["condition_label"])
        <= MAX_CONSECUTIVE_SAME_COND
        and _max_run_by_key(test_sequence, lambda item: item["family"])
        <= MAX_CONSECUTIVE_SAME_FAMILY
        and _max_run_by_key(test_sequence, lambda item: item["position"])
        <= MAX_CONSECUTIVE_SAME_POSITION
    )


def _position_counts_for_condition(
    n_per_block: int,
    condition_index: int,
    block_index: int,
    n_blocks: int,
) -> tuple[int, int]:
    """Return upper and lower counts while balancing odd counts across blocks."""
    base_count = n_per_block // 2

    if n_per_block % 2 == 0:
        return base_count, base_count

    if n_blocks % 2 != 0:
        raise ValueError(
            "Odd n_per_block values require an even number of blocks to obtain "
            "exact upper/lower balance across the experiment."
        )

    extra_upper = (condition_index + block_index) % 2 == 0
    if extra_upper:
        return base_count + 1, base_count
    return base_count, base_count + 1


def _build_trials_for_block(
    block_index: int,
    condition_specs: ConditionSpecs = CONDITION_SPECS,
    n_blocks: int = N_BLOCKS,
) -> list[TrialSpec]:
    trials: list[TrialSpec] = []

    for condition_index, (condition_label, spec) in enumerate(
        condition_specs.items()
    ):
        n_per_block = int(spec["n_per_block"])
        if n_per_block <= 0:
            raise ValueError(
                f"Condition {condition_label!r} has invalid "
                f"n_per_block={n_per_block}."
            )

        n_upper, n_lower = _position_counts_for_condition(
            n_per_block=n_per_block,
            condition_index=condition_index,
            block_index=block_index,
            n_blocks=n_blocks,
        )

        for position, count in (("upper", n_upper), ("lower", n_lower)):
            for _ in range(count):
                trials.append(
                    {
                        "condition_label": condition_label,
                        "base_condition": spec["base_condition"],
                        "soa_ms": float(spec["soa_ms"]),
                        "soa_type": spec["soa_type"],
                        "correct_answer": spec["correct_answer"],
                        "family": spec["family"],
                        "illusion_type": spec.get("illusion_type", "none"),
                        "position": position,
                    }
                )

    return trials


def _generate_valid_block(
    block_index: int,
    condition_specs: ConditionSpecs = CONDITION_SPECS,
    n_blocks: int = N_BLOCKS,
    rng: random.Random | Any = random,
) -> list[TrialSpec]:
    base_trials = _build_trials_for_block(
        block_index=block_index,
        condition_specs=condition_specs,
        n_blocks=n_blocks,
    )

    for _ in range(MAX_BUILD_ATTEMPTS):
        remaining = base_trials.copy()
        sequence: list[TrialSpec] = []

        while remaining:
            candidates = [
                trial for trial in remaining if _valid_extension(sequence, trial)
            ]
            if not candidates:
                break

            trial = rng.choice(candidates)
            sequence.append(trial)
            remaining.remove(trial)

        if not remaining:
            return sequence

    raise RuntimeError(
        "Unable to generate a block satisfying the randomization constraints. "
        "Review the condition counts or the MAX_CONSECUTIVE_* limits."
    )


def generate_blocks(
    condition_specs: ConditionSpecs = CONDITION_SPECS,
    n_blocks: int = N_BLOCKS,
    rng: random.Random | Any = random,
) -> list[list[TrialSpec]]:
    """Generate all blocks for the selected design."""
    if n_blocks <= 0:
        raise ValueError("n_blocks must be greater than zero.")

    return [
        _generate_valid_block(
            block_index=block_index,
            condition_specs=condition_specs,
            n_blocks=n_blocks,
            rng=rng,
        )
        for block_index in range(n_blocks)
    ]
