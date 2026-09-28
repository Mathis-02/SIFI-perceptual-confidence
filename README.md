# Sound-induced flash illusion and perceptual confidence

This repository contains the experimental task and analysis pipeline developed during my Master's internship in cognitive science at the Grenoble Institute of Neuroscience.

The project investigated whether perceptual confidence depends not only on what is perceived, but also on whether the percept is physically presented or induced by multisensory integration. I used the sound-induced flash illusion (SIFI) to compare confidence for matched physical and illusory percepts.

The full Master's thesis is available in French: [Master's thesis (PDF)](master_thesis_FR.pdf)

## Experiment

The final experiment combined fission and fusion variants of the SIFI at two audiovisual stimulus onset asynchronies (SOAs):

- standard SOA: 83 ms;
- short SOA: 50 ms.

Participants first reported whether they perceived one or two flashes and then rated their confidence on a continuous scale from 50% to 100%.

The final sample included 9 participants. Each participant completed 8 blocks of 72 trials, for a total of 576 trials per participant and 5,184 trials across the experiment.

The PsychoPy task implements constrained trial randomization, stimulus timing, trial-by-trial logging, session summaries, acquisition checks, and tools for photodiode-based timing validation. Seeded unit tests verify the trial sequences and randomization constraints.

See [`experimental_task/`](experimental_task/) for the acquisition code and documentation.

## Analysis

The analysis pipeline combines Python and R.

Python is used for data validation, preprocessing, descriptive statistics, quality control, and figure generation. The main inferential analyses use mixed-effects models in R, with supplementary hierarchical meta-d analyses for metacognitive efficiency.

The main analyses compare confidence between physically presented and illusory percepts while holding the reported number of flashes constant.

See [`analyses/`](analyses/) for the analysis code, statistical outputs, diagnostics, and detailed documentation.

## Main results

The audiovisual manipulation strongly affected perceptual reports across experimental conditions (binomial GLMM, likelihood-ratio test: χ²(6) = 2732.76, p < .001).

For trials in which participants reported two flashes, confidence was lower for illusory fission percepts than for physically presented two-flash percepts. The difference depended on SOA (origin × SOA: χ²(1) = 29.66, p < .001):

- standard SOA: illusory − physical = −8.71 confidence points;
- short SOA: illusory − physical = −2.40 points.

For trials in which participants reported one flash, confidence also differed between physical and fusion-related percepts (χ²(2) = 165.62, p < .001):

- standard-SOA fusion: illusory − physical = −12.13 points;
- short-SOA fusion: illusory − physical = −6.45 points.

These results show that matched perceptual reports can be associated with different levels of confidence depending on the sensory conditions that generated them.

Selected figures:

- [Fission and fusion illusion rates by SOA](analyses/outputs/figures/perceptual/02_illusion_rate_fission_fusion_by_soa.pdf)
- [Matched-percept confidence analyses](analyses/outputs/figures/confidence/03_confidence_composite_abcd.pdf)

## Repository structure

- [`experimental_task/`](experimental_task/) — final PsychoPy experiment, configuration, acquisition utilities, and tests.
- [`analyses/`](analyses/) — preprocessing, statistical analyses, diagnostics, tables, and figures.

Each directory contains its own README with installation and execution instructions.

## Data and reproducibility

Participant-level experimental data are not distributed in this public repository. The `analyses/data/` directory documents the expected input structure, while selected derived tables, figures, and statistical outputs are retained.

The complete analysis pipeline therefore requires access to the original participant-level data.

One historical supplementary congruent-baseline HMeta-d analysis is retained as derived output, but its original implementation is no longer available. Its retained diagnostic report records 19 divergent NUTS transitions. This limitation is documented in the analysis directory.

No participant identity keys, consent forms, contact details, or identifying session notes are included in this repository.
