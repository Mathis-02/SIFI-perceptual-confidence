"""Shared escape-key handling."""

from psychopy import event


class ExperimentAbort(Exception):
    """Raised when the participant or experimenter stops the session."""


def check_abort() -> None:
    """Raise ExperimentAbort when Escape is pressed."""
    if "escape" in event.getKeys(keyList=["escape"]):
        raise ExperimentAbort("User aborted (escape)")
