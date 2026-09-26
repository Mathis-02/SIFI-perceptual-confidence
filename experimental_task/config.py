"""Configuration for the sound-induced flash illusion experiment.

Edit the constants in this file before starting a data-collection session. The
three experimental designs are retained because they correspond to successive
versions of the task used during development and piloting.
"""

# -----------------------------------------------------------------------------
# Experiment mode
# -----------------------------------------------------------------------------
CODE_VERSION = "v1.0.0_final"
#PILOT_MODE=True runs the full eight-block
# protocol, while False runs a two-block shortened session.
PILOT_MODE = True

# Available values:
#   "standard_4cond"            original four-condition design
#   "short_soa_6cond"           six-condition design with a short SOA
#   "av_fission_fusion_2soa"    final multisensory fission/fusion design
DESIGN_MODE = "av_fission_fusion_2soa"

DEBUG_MODE = False
LAB_MODE = True 
RNG_SEED = None


N_BLOCKS = 8 if PILOT_MODE else 2

# Conditions used in practice for the "standard_4cond" and ""short_soa_6cond" designs."av_fission_fusion_2soa" design
# selects its own four audiovisual practice conditions in core/start_phase.py.
CONDITIONS = ["V1", "V1V2", "A1V1_A2", "A1V1_A2V2"]

# -----------------------------------------------------------------------------
# Experimental designs
# -----------------------------------------------------------------------------

SOA_MS = 83
SHORT_SOA_MS = 50

STANDARD_4COND_SPECS = {
    "V1": {
        "base_condition": "V1",
        "n_per_block": 18,
        "soa_ms": SOA_MS,
        "soa_type": "standard",
        "correct_answer": "1",
        "family": "visual",
        "illusion_type": "none",
    },
    "V1V2": {
        "base_condition": "V1V2",
        "n_per_block": 18,
        "soa_ms": SOA_MS,
        "soa_type": "standard",
        "correct_answer": "2",
        "family": "visual",
        "illusion_type": "none",
    },
    "A1V1_A2": {
        "base_condition": "A1V1_A2",
        "n_per_block": 18,
        "soa_ms": SOA_MS,
        "soa_type": "standard",
        "correct_answer": "1",
        "family": "audiovisual",
        "illusion_type": "fission",
    },
    "A1V1_A2V2": {
        "base_condition": "A1V1_A2V2",
        "n_per_block": 18,
        "soa_ms": SOA_MS,
        "soa_type": "standard",
        "correct_answer": "2",
        "family": "audiovisual",
        "illusion_type": "none",
    },
}

SHORT_SOA_6COND_SPECS = {
    "V1_standard": {
        "base_condition": "V1",
        "n_per_block": 18,
        "soa_ms": SOA_MS,
        "soa_type": "standard",
        "correct_answer": "1",
        "family": "visual_1flash",
        "illusion_type": "none",
    },
    "A1V1_A2_standard": {
        "base_condition": "A1V1_A2",
        "n_per_block": 18,
        "soa_ms": SOA_MS,
        "soa_type": "standard",
        "correct_answer": "1",
        "family": "av_illusion",
        "illusion_type": "fission",
    },
    "V1V2_standard": {
        "base_condition": "V1V2",
        "n_per_block": 9,
        "soa_ms": SOA_MS,
        "soa_type": "standard",
        "correct_answer": "2",
        "family": "visual_2flash",
        "illusion_type": "none",
    },
    "V1V2_short": {
        "base_condition": "V1V2",
        "n_per_block": 9,
        "soa_ms": SHORT_SOA_MS,
        "soa_type": "short",
        "correct_answer": "2",
        "family": "visual_2flash",
        "illusion_type": "none",
    },
    "A1V1_A2V2_standard": {
        "base_condition": "A1V1_A2V2",
        "n_per_block": 9,
        "soa_ms": SOA_MS,
        "soa_type": "standard",
        "correct_answer": "2",
        "family": "av_congruent",
        "illusion_type": "none",
    },
    "A1V1_A2V2_short": {
        "base_condition": "A1V1_A2V2",
        "n_per_block": 9,
        "soa_ms": SHORT_SOA_MS,
        "soa_type": "short",
        "correct_answer": "2",
        "family": "av_congruent",
        "illusion_type": "none",
    },
}

AV_FISSION_FUSION_2SOA_SPECS = {
    "A1V1": {
        "base_condition": "A1V1",
        "n_per_block": 18,
        "soa_ms": SOA_MS,
        "soa_type": "standard",
        "correct_answer": "1",
        "family": "av_1flash",
        "illusion_type": "none",
    },
    "A1V1_A2_short": {
        "base_condition": "A1V1_A2",
        "n_per_block": 9,
        "soa_ms": SHORT_SOA_MS,
        "soa_type": "short",
        "correct_answer": "1",
        "family": "av_1flash",
        "illusion_type": "fission",
    },
    "A1V1_A2_standard": {
        "base_condition": "A1V1_A2",
        "n_per_block": 9,
        "soa_ms": SOA_MS,
        "soa_type": "standard",
        "correct_answer": "1",
        "family": "av_1flash",
        "illusion_type": "fission",
    },
    "A1V1_V2_short": {
        "base_condition": "A1V1_V2",
        "n_per_block": 9,
        "soa_ms": SHORT_SOA_MS,
        "soa_type": "short",
        "correct_answer": "2",
        "family": "av_2flash",
        "illusion_type": "fusion",
    },
    "A1V1_V2_standard": {
        "base_condition": "A1V1_V2",
        "n_per_block": 9,
        "soa_ms": SOA_MS,
        "soa_type": "standard",
        "correct_answer": "2",
        "family": "av_2flash",
        "illusion_type": "fusion",
    },
    "A1V1_A2V2_short": {
        "base_condition": "A1V1_A2V2",
        "n_per_block": 9,
        "soa_ms": SHORT_SOA_MS,
        "soa_type": "short",
        "correct_answer": "2",
        "family": "av_2flash",
        "illusion_type": "none",
    },
    "A1V1_A2V2_standard": {
        "base_condition": "A1V1_A2V2",
        "n_per_block": 9,
        "soa_ms": SOA_MS,
        "soa_type": "standard",
        "correct_answer": "2",
        "family": "av_2flash",
        "illusion_type": "none",
    },
}

CONDITION_SPECS_BY_DESIGN = {
    "standard_4cond": STANDARD_4COND_SPECS,
    "short_soa_6cond": SHORT_SOA_6COND_SPECS,
    "av_fission_fusion_2soa": AV_FISSION_FUSION_2SOA_SPECS,
}

try:
    CONDITION_SPECS = CONDITION_SPECS_BY_DESIGN[DESIGN_MODE]
except KeyError as exc:
    valid_modes = ", ".join(CONDITION_SPECS_BY_DESIGN)
    raise ValueError(
        f"Unknown DESIGN_MODE {DESIGN_MODE!r}. Valid values: {valid_modes}."
    ) from exc

TRIALS_PER_BLOCK = sum(
    int(spec["n_per_block"]) for spec in CONDITION_SPECS.values()
)
TRIALS_TOTAL = TRIALS_PER_BLOCK * N_BLOCKS

# -----------------------------------------------------------------------------
# Laboratory setup
# -----------------------------------------------------------------------------

LAB_VIEWING_DISTANCE_CM = 60.0
LAB_SCREEN_WIDTH_CM = 34.46
MAX_ACCEPTABLE_IQR_CM = 8.0
SCREEN_REFRESH = 60

# -----------------------------------------------------------------------------
# Stimuli and timing
# -----------------------------------------------------------------------------

# Keep the fixation cross visible while the auditory and visual stimuli are presented. 
# Set to False to hide the fixation cross during stimulus presentation.
KEEP_FIXATION_DURING_STIM = True
POST_STIM_BLANK_MS = 600
FIXATION_MIN = 1.0
FIXATION_MAX = 1.5

FLASH_DIAMETER_DEG = 1.0
FLASH_ECCENTRICITY_DEG = 6.0
FLASH_DURATION_MS = 17
FLASH_INTENSITY = 1.0

# Select the auditory stimulus source.
# False: generate a pure tone with PsychoPy using BEEP_FREQ and BEEP_DURATION.
# True: load the prerecorded stimulus specified by BEEP_WAV_FILENAME
# from the sounds/ directory. The WAV file must be distributed with the task.
USE_WAV_BEEP = True
BEEP_WAV_FILENAME = "Beep2.wav"
TONE_FREQUENCY = 1000
TONE_DURATION_MS = 10
AUDIO_SAMPLE_RATE = 48000
AUDIO_VOLUME = 1.0
AUDIO_RAMP_MS = 1.0
REQUIRE_HEADPHONES = False

# -----------------------------------------------------------------------------
# Confidence response
# -----------------------------------------------------------------------------

# Select the confidence response format. # "continuous": continuous scale bounded from 50% to 100%. 
# "discrete": four-level confidence scale with responses from 1 to 4.
CONFIDENCE_MODE = "continuous"  # "discrete" or "continuous"
CONF_MIN = 50
CONF_MAX = 100
CONF_START = 75
CONF_STEP_KEY = 1
CONF_LABEL_LEFT = "50%"
CONF_LABEL_RIGHT = "100%"

# Number-row key names returned by PsychoPy on AZERTY keyboards.
CONF_KEYS = ["1", "2", "3", "4", "&", "é", '"', "'"]
