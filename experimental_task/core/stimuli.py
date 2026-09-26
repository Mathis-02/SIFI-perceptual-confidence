"""Visual and auditory stimulus construction."""

from pathlib import Path

import numpy as np
from psychopy import visual, sound
from psychopy.sound import AudioClip

from config import (
    FLASH_DIAMETER_DEG,
    FLASH_ECCENTRICITY_DEG,
    FLASH_INTENSITY,
    TONE_FREQUENCY,
    TONE_DURATION_MS,
    AUDIO_SAMPLE_RATE,
    AUDIO_VOLUME,
    AUDIO_RAMP_MS,
    USE_WAV_BEEP,
    BEEP_WAV_FILENAME,
)


def intensity_to_rgb_level(intensity: float) -> float:
    intensity = max(0.0, min(1.0, float(intensity)))
    return -1.0 + 2.0 * intensity


def create_flash(win, position="upper"):
    if position == "upper":
        y_pos = FLASH_ECCENTRICITY_DEG
    elif position == "lower":
        y_pos = -FLASH_ECCENTRICITY_DEG
    else:
        raise ValueError("position must be 'upper' or 'lower'.")

    col = intensity_to_rgb_level(FLASH_INTENSITY)

    return visual.Circle(
        win=win,
        radius=FLASH_DIAMETER_DEG / 2.0,
        fillColor=[col, col, col],
        lineColor=[col, col, col],
        pos=(0, y_pos),
        units="deg"
    )


def _make_tone_waveform(
    freq_hz: float,
    duration_ms: float,
    sample_rate: int,
    volume: float,
    ramp_ms: float
) -> np.ndarray:
    if duration_ms <= 0:
        raise ValueError("duration_ms must be > 0")
    if sample_rate <= 0:
        raise ValueError("sample_rate must be > 0")
    if not (0.0 <= volume <= 1.0):
        raise ValueError("volume must be between 0.0 and 1.0")
    if freq_hz <= 0:
        raise ValueError("freq_hz must be > 0")
    if freq_hz >= sample_rate / 2:
        raise ValueError("freq_hz must be below Nyquist frequency")

    n_samples = int(round(sample_rate * duration_ms / 1000.0))
    n_samples = max(1, n_samples)

    t = np.arange(n_samples, dtype=np.float32) / np.float32(sample_rate)

    wave = np.sin(2 * np.pi * np.float32(freq_hz) * t).astype(np.float32)

    # Short raised-cosine ramps suppress onset and offset clicks.
    ramp_samples = int(round(sample_rate * ramp_ms / 1000.0))
    ramp_samples = max(0, min(ramp_samples, n_samples // 2))

    if ramp_samples > 0:
        ramp = 0.5 * (
            1.0 - np.cos(np.linspace(0, np.pi, ramp_samples, dtype=np.float32))
        )
        envelope = np.ones(n_samples, dtype=np.float32)
        envelope[:ramp_samples] = ramp
        envelope[-ramp_samples:] = ramp[::-1]
        wave *= envelope

    wave *= np.float32(volume)

    stereo = np.column_stack((wave, wave)).astype(np.float32)

    # PsychoPy expects a contiguous samples-by-channels array.
    stereo = np.ascontiguousarray(stereo, dtype=np.float32)

    return stereo


def create_tone():
    if USE_WAV_BEEP:
        project_root = Path(__file__).resolve().parent.parent
        sound_path = project_root / "sounds" / BEEP_WAV_FILENAME
        if not sound_path.is_file():
            raise FileNotFoundError(f"Beep file not found: {sound_path}")

        tone = sound.Sound(
            value=str(sound_path),
            stereo=True
        )
        return tone

    waveform = _make_tone_waveform(
        freq_hz=TONE_FREQUENCY,
        duration_ms=TONE_DURATION_MS,
        sample_rate=AUDIO_SAMPLE_RATE,
        volume=AUDIO_VOLUME,
        ramp_ms=AUDIO_RAMP_MS,
    )

    clip = AudioClip(waveform, sampleRateHz=AUDIO_SAMPLE_RATE)

    tone = sound.Sound(
        value=clip,
        stereo=True,
        sampleRate=AUDIO_SAMPLE_RATE
    )

    return tone
