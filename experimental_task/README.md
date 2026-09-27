# Sound-Induced Flash Illusion experiment

This repository contains the PsychoPy acquisition task used to study fission and fusion variants of the sound-induced flash illusion and the confidence judgments associated with each perceptual report.

The repository contains acquisition and quality-control code only. Inferential statistics, figures, signal-detection analyses, and metacognitive analyses are intentionally maintained in a separate analysis project.

## Experimental designs

Select the design in `config.py` by setting `DESIGN_MODE` to one of the three values described below.

### Condition notation

`A` denotes an auditory beep and `V` denotes a visual flash. The indices `1` and `2` identify the first and second stimulus events. Stimuli that share an index are presented synchronously. For example, `A1V1_A2` consists of a synchronous beep-flash event followed by a second beep without a second flash. The underscore separates the first and second events.

For conditions containing two events, the stimulus onset asynchrony (SOA) is the onset-to-onset interval between the first and second events. The standard SOA is 83 ms and the short SOA is 50 ms. The correct response refers to the number of flashes physically presented, irrespective of the participant's perceptual report.

### `standard_4cond`

This is the original four-condition design. Each condition occurs 18 times per block.

| Condition | Physical sequence | Correct response | Experimental role |
| --- | --- | --- | --- |
| `V1` | One visual flash | 1 flash | Single-flash visual baseline |
| `V1V2` | Two visual flashes separated by the standard SOA | 2 flashes | Two-flash visual baseline |
| `A1V1_A2` | One synchronous beep-flash event followed by a second beep | 1 flash | Fission condition. A report of 2 flashes is classified as a fission illusion |
| `A1V1_A2V2` | Two synchronous beep-flash events separated by the standard SOA | 2 flashes | Congruent audiovisual control |

This design contains 72 trials per block and does not include a fusion condition.

### `short_soa_6cond`

This six-condition design introduced the 50 ms SOA while retaining the original fission condition at 83 ms.

| Condition | Trials per block | Physical sequence | Correct response | Experimental role |
| --- | ---: | --- | --- | --- |
| `V1_standard` | 18 | One visual flash | 1 flash | Single-flash visual baseline. No second event is presented; the `standard` label is retained for compatibility with the original design |
| `A1V1_A2_standard` | 18 | One synchronous beep-flash event followed by a second beep at 83 ms | 1 flash | Fission condition. A report of 2 flashes is classified as a fission illusion |
| `V1V2_standard` | 9 | Two visual flashes separated by 83 ms | 2 flashes | Standard-SOA visual control |
| `V1V2_short` | 9 | Two visual flashes separated by 50 ms | 2 flashes | Short-SOA visual control |
| `A1V1_A2V2_standard` | 9 | Two synchronous beep-flash events separated by 83 ms | 2 flashes | Standard-SOA congruent audiovisual control |
| `A1V1_A2V2_short` | 9 | Two synchronous beep-flash events separated by 50 ms | 2 flashes | Short-SOA congruent audiovisual control |

This design contains 72 trials per block. It manipulates the SOA in the two-flash visual and congruent audiovisual controls, but the fission condition is presented only at the standard SOA. It does not include a fusion condition.

### `av_fission_fusion_2soa`

This is the final multisensory design. The first event is audiovisual in every condition, and fission, fusion, and congruent conditions are presented at both SOAs.

| Condition | Trials per block | Physical sequence | Correct response | Experimental role |
| --- | ---: | --- | --- | --- |
| `A1V1` | 18 | One synchronous beep-flash event | 1 flash | Single-event audiovisual baseline. No second event is presented |
| `A1V1_A2_short` | 9 | One synchronous beep-flash event followed by a second beep at 50 ms | 1 flash | Short-SOA fission condition. A report of 2 flashes is classified as a fission illusion |
| `A1V1_A2_standard` | 9 | One synchronous beep-flash event followed by a second beep at 83 ms | 1 flash | Standard-SOA fission condition. A report of 2 flashes is classified as a fission illusion |
| `A1V1_V2_short` | 9 | One synchronous beep-flash event followed by a second flash at 50 ms | 2 flashes | Short-SOA fusion condition. A report of 1 flash is classified as a fusion illusion |
| `A1V1_V2_standard` | 9 | One synchronous beep-flash event followed by a second flash at 83 ms | 2 flashes | Standard-SOA fusion condition. A report of 1 flash is classified as a fusion illusion |
| `A1V1_A2V2_short` | 9 | Two synchronous beep-flash events separated by 50 ms | 2 flashes | Short-SOA congruent audiovisual control |
| `A1V1_A2V2_standard` | 9 | Two synchronous beep-flash events separated by 83 ms | 2 flashes | Standard-SOA congruent audiovisual control |

This design contains 72 trials per block. The session summaries define the fission rate as the proportion of `2 flash` responses in `A1V1_A2` trials and the fusion rate as the proportion of `1 flash` responses in `A1V1_V2` trials. Confidence is summarized separately for illusion and no-illusion reports within each condition and SOA.

All three designs retain their original condition counts and constrained randomization. With the current full-session configuration, each design produces 8 blocks of 72 trials, for 576 trials in total.

`PILOT_MODE`, `True` runs 8 blocks and `False` runs a shortened 2-block session.

## Randomization constraints

Trial order is generated separately for each block in `core/experiment.py`. The following constants limit consecutive repetitions:

```python
MAX_CONSECUTIVE_SAME_COND = 3
MAX_CONSECUTIVE_SAME_FAMILY = 6
MAX_CONSECUTIVE_SAME_POSITION = 3
MAX_BUILD_ATTEMPTS = 5000
```

`MAX_CONSECUTIVE_SAME_COND` is the largest permitted run of the same exact condition label. With the default value of 3, a condition such as `A1V1_A2_short` cannot occur more than three times consecutively.

`MAX_CONSECUTIVE_SAME_FAMILY` limits consecutive trials belonging to the same broader condition family. Families are assigned in `config.py` and group related conditions beyond their exact labels. In the final design, for example, the fission and single-event conditions belong to the `av_1flash` family, whereas fusion and congruent two-event conditions belong to the `av_2flash` family. The default value of 6 prevents an extended run from the same broad stimulus category even when the exact condition labels differ.

`MAX_CONSECUTIVE_SAME_POSITION` limits consecutive presentations in the same visual field position. With the default value of 3, no more than three successive trials can use `upper` or `lower` presentation. This run-length restriction is separate from the exact upper/lower count balance enforced across the experiment.

`MAX_BUILD_ATTEMPTS` is the maximum number of complete attempts used to construct one valid block. If an attempt reaches a point where no remaining trial can be added without violating a constraint, that partial sequence is discarded and construction restarts. The task raises an explicit error if no valid block is found after 5000 attempts.

These values affect trial order only. They do not change the number of blocks or the number of trials assigned to each condition. Lower limits produce stricter randomization and can make block construction impossible, particularly after changing `n_per_block` values or condition proportions. Increasing `MAX_BUILD_ATTEMPTS` allows more construction attempts but does not relax the constraints. After changing any of these values, run the automated tests and complete a short test session before data collection.

## Execution modes and display calibration

The acquisition setup is selected with `LAB_MODE` in `config.py`. This setting changes how the monitor geometry and viewing distance are established. It does not change the experimental design selected by `DESIGN_MODE`.

### Fixed ThinkPad laboratory setup

Set:

```python
LAB_MODE = True
```

Use this mode for data collection on the laboratory ThinkPad 21QV with the validated fixed setup. The task uses the laboratory constants defined in `config.py`:

- screen width: 34.46 cm;
- viewing distance: 60 cm;
- expected refresh rate: 60 Hz.

The initial monitor resolution is set to 1920 × 1200 pixels and is then updated from the actual full-screen PsychoPy window. The bank-card screen calibration, audio setup screen, visual display check, and blind-spot distance calibration are skipped because the hardware geometry and viewing distance are assumed to match the validated laboratory setup.

Practice is supervised manually in this mode. After each practice phase, the mean error rate for the key physical baseline conditions is displayed as a small percentage in the upper-left corner. The experimenter must press:

- `o` to repeat the current practice phase;
- `p` to continue to the next phase or the main experiment;
- `Escape` to abort.

These manual controls are used only when `LAB_MODE = True`. A poor practice score therefore does not trigger an automatic participant-facing retry screen in laboratory mode. This is intentional: the experimenter decides whether the phase should be repeated. For the final multisensory design, the supervision score is based on `A1V1` and `A1V1_A2V2`. For the earlier designs, it is based on `V1` and `V1V2`.

### Multi-device adaptive setup

Set:

```python
LAB_MODE = False
```

Use this mode when the task must adapt to another computer or display. The setup then includes:

1. bank-card calibration to estimate the physical screen width;
2. audio-volume adjustment;
3. visual display and luminance check;
4. blind-spot calibration to estimate viewing distance;
5. a second blind-spot measurement when the first estimate is unreliable;
6. a 60 cm fallback distance if both blind-spot estimates fail the quality criteria.

The calibrated screen width, resolution, viewing distance, calibration method, number of valid blind-spot trials, and distance-estimate variability are stored in the session metadata. Participants also receive additional instructions to preserve their calibrated position and avoid changing the audio or display settings during the experiment.

Practice evaluation is automatic in this mode. The `o` and `p` supervision keys are not used. Accuracy below 75% in either key physical baseline condition, or insufficient use of the confidence scale, displays an explanatory feedback screen and triggers one additional practice series automatically. For the final multisensory design, baseline accuracy is evaluated from `A1V1` and `A1V1_A2V2`; for the earlier designs, it is evaluated from `V1` and `V1V2`. After this single additional series, the task proceeds to the main experiment without a second automatic evaluation.

### Debug mode

`DEBUG_MODE = True` uses a fixed test monitor and skips the instruction and practice sequence. It is intended for software checks only and must not be used for data collection.

## Installation

The laboratory version was developed with PsychoPy 2026.1.1. A dedicated PsychoPy environment is recommended.

```bash
python -m pip install -r requirements.txt
```

The task uses the Psychtoolbox audio backend. Audio preferences are configured before PsychoPy sound modules are imported.

## Auditory stimulus

The final experimental protocol uses the validated prerecorded auditory stimulus Beep2.wav.

The file must be placed in the sounds/ directory at the project root:

sounds/Beep2.wav

Keep the following configuration:

USE_WAV_BEEP = True
BEEP_WAV_FILENAME = "Beep2.wav"

If USE_WAV_BEEP is set to False, PsychoPy generates a pure tone using BEEP_FREQ and BEEP_DURATION instead of loading the WAV file. This fallback tone has not been used for the validated final laboratory protocol.

## Changing the number of blocks and trials

The number of blocks and the number of trials assigned to each condition are configured in `config.py`.

### Number of blocks

The total number of experimental blocks is controlled by `N_BLOCKS`:

```python
N_BLOCKS = 8
```

Changing this value changes the total number of trials without changing the number of trials presented within each block.

For example:

```python
N_BLOCKS = 4
```

runs four experimental blocks.

If `N_BLOCKS` is currently defined from another setting, such as:

```python
N_BLOCKS = 8 if PILOT_MODE else 2
```

both values can be edited, or the expression can be replaced by a fixed value.

### Number of trials per condition

The number of trials assigned to each condition within one block is defined by the `n_per_block` field in the specification of the selected design.

For the final multisensory design:

```python
DESIGN_MODE = "av_fission_fusion_2soa"
```

edit the values in:

```python
AV_FISSION_FUSION_2SOA_SPECS
```

For example:

```python
"A1V1": {
    "n_per_block": 18,
    ...
},
"A1V1_A2_short": {
    "n_per_block": 9,
    ...
},
```

The total number of trials per block is calculated automatically as the sum of all `n_per_block` values:

```python
TRIALS_PER_BLOCK = sum(
    int(spec["n_per_block"]) for spec in CONDITION_SPECS.values()
)
```

The total number of trials in the experiment is then calculated automatically:

```python
TRIALS_TOTAL = TRIALS_PER_BLOCK * N_BLOCKS
```

`TRIALS_PER_BLOCK` and `TRIALS_TOTAL` should therefore not be edited directly.

With the default final design:

```text
18 baseline trials + 6 × 9 other trials = 72 trials per block
72 trials per block × 8 blocks = 576 trials
```

### Constraints

Trial counts must remain compatible with the balancing and randomization rules.

Visual stimuli are balanced between the upper and lower positions across the full experiment. A condition must therefore have an even total number of trials across all blocks:

```text
n_per_block × N_BLOCKS
```

must be even for each condition.

For example, a condition with 9 trials per block requires an even number of blocks:

```text
9 × 8 = 72
```

is compatible with exact position balancing, whereas:

```text
9 × 3 = 27
```

cannot be divided equally between the two visual positions.

Condition counts should also remain sufficiently balanced. A condition or condition family that represents too large a proportion of a block may make it impossible to satisfy the restrictions on consecutive repetitions.

After changing the design, run the automated checks:

```bash
python -m unittest discover -s tests
```

Also verify the values printed at task startup, including:

```text
Number of blocks
Trials per block
Total number of trials
Trials per condition
```

Changes to trial counts should be validated in a short test session before data collection.


## Running the experiment

From the `experimental_task/` directory, review `config.py`, then start the task:

```bash
python main.py
```

Participant-facing instructions remain in French. Code comments, docstrings, technical identifiers, and repository documentation are in English.

The participant identifier is sanitized before it is used in a filename. Existing trial files are never overwritten. A new identifier must be used for each acquisition session.

## Output files

The task writes trial data to:

```text
data/trials/<participant>_trials.csv
```

Session metadata and acquisition summaries are written to:

```text
data/session_info/<participant>_session.csv
data/session_info/<participant>_condition_summary.csv
data/session_info/<participant>_block_summary.csv
```

The trial file is flushed after every trial. It retains the original 48-column schema, including physical condition, perceptual response, confidence, event timing, estimated dropped frames, and any trial-level error.

The condition summary reports, when applicable:

- fission and fusion rates for each SOA;
- mean confidence for illusion and no-illusion responses;
- the standard deviation of blockwise illusion rates and confidence means;
- dropped-frame frequency;
- visual SOA, scheduled audio SOA, and blank-ISI timing errors.

The block summary provides the corresponding descriptive measures for each condition within each block. These summaries are intended for immediate acquisition quality control and are not substitutes for the separate statistical analysis pipeline.

## Timing utilities

Additional utilities are stored in `tools/`.

- `demo_obs_fullscreen.py` presents a windowed demonstration of the four audiovisual structures.
- `test_photodiode.py` supports external timing validation with a photodiode and oscilloscope.

From the `experimental_task/` directory, run a utility, for example:

```bash
python tools/test_photodiode.py
```

## Automated checks

The test suite validates the three experimental designs, seeded sequence compatibility, condition counts, randomization constraints, position balance, timing conversion, trial logging, participant identifiers, and illusion-summary definitions.

```bash
python -m unittest discover -s tests -v
```

Automated tests do not replace validation on the acquisition computer. Hardware timing, display, and audio should be checked on the acquisition computer before collecting new data.

## Project structure

* `main.py` starts the experiment, initializes the session, runs the selected experimental design, and saves the session outputs.
* `config.py` contains the experimental design, timing, display, audio, practice, and randomization settings.
* `core/abort.py` handles controlled experiment interruption and resource cleanup.
* `core/calibration.py` contains the screen-size, viewing-distance, audio, and visual calibration procedures used outside the fixed laboratory setup.
* `core/experiment.py` builds the experimental blocks and applies the trial-order randomization constraints.
* `core/start_phase.py` runs the instructions, practice trials, and practice-performance checks.
* `core/stimuli.py` creates the visual stimuli, fixation cross, response displays, confidence scale, and auditory stimulus.
* `core/timing.py` converts requested durations into display frames and provides timing utilities.
* `core/trial.py` presents one experimental trial and records the perceptual response, confidence rating, and timing information.
* `core/trial_logger.py` writes trial-level data to the CSV file in `data/trials/`.
* `core/session_summary.py` computes and saves descriptive session-level, condition-level, and block-level quality-control summaries.
* `core/window.py` creates and configures the PsychoPy window and measures the display refresh period.
* `sounds/` contains the prerecorded auditory stimulus used by the validated final protocol.
* `tests/` contains automated tests for the experimental designs, randomization constraints, timing conversions, CSV structure, and session summaries.
* `data/trials/` receives the raw trial-level CSV files.
* `data/session_info/` receives session metadata and descriptive quality-control summaries.


