# SIFI multisensory analysis

Reproducible analysis repository for the multisensory sound-induced flash illusion (SIFI) study.

The repository contains Python preprocessing and descriptive analyses, R mixed-effects models, hierarchical meta-d analyses, diagnostic outputs, statistical tables, and generated figures. Participant-level experimental data are not included in the public repository.

## Scientific scope

The study examines perceptual reports and confidence in fission and fusion SIFI conditions at standard and short stimulus-onset asynchronies (SOAs).

The primary analyses are:

1. A binomial generalized linear mixed model (GLMM) for the probability of reporting two flashes.
2. A Gaussian linear mixed model (LMM) comparing confidence for matched two-flash reports of physical or illusory origin.
3. A Gaussian LMM comparing confidence for matched one-flash reports in congruent and fusion conditions.

Beta-family sensitivity analyses and hierarchical meta-d analyses are supplementary.

Participant-level correlations, block analyses, and associations involving individual M-ratio estimates are exploratory.

## Repository structure

```text
data/trials/                 Expected location of participant trial files (not distributed)
scripts/                     Python entry points
scripts/R/                   R inferential and supplementary analyses
scripts/R/hmetad/            Hierarchical meta-d and M-ratio analyses
src/                         Reusable Python modules
outputs/figures/             Generated manuscript and supplementary figures
outputs/tables/              Selected descriptive, inferential, and diagnostic tables
outputs/reports/             Model summaries and quality-control reports
```

## Data status

Participant-level experimental data are not distributed in this public repository. The analysis scripts expect the original trial files in `data/trials/`.

The analyses were developed on pseudonymized data from the main experiment. Pilot data are not part of this analysis directory.

Do not add participant-code linkage keys, consent forms, recruitment files, contact information, or identifying session notes to the repository.

## Software dependencies

Python and R dependencies are managed separately.

* `requirements.txt` contains only the Python packages required for preprocessing, descriptive analyses, quality control, and figure generation.
* `scripts/R/install_packages.R` installs the CRAN packages required for mixed models, diagnostics, sensitivity analyses, and hierarchical meta-d analyses. The `hmetad` package must be installed separately using the installation procedure provided by its authors.

R packages are not listed in `requirements.txt`, because that file is specific to Python package managers such as `pip`.

## Quick start

### Python preprocessing and descriptive outputs

Create a Python virtual environment and install the required packages:

```bash
python -m venv .venv
```

On Windows:

```bash
.venv\Scripts\activate
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Run the full Python pipeline from the repository root:

```bash
python scripts/run_all.py
```

The Python pipeline:

* validates the trial-level CSV files;
* rebuilds the processed datasets;
* recodes analysis variables;
* exports descriptive tables;
* generates manuscript figures;
* prepares model-ready subsets;
* produces quality-control outputs.

### R inferential analyses

The main R dependencies include:

* `readr`, `dplyr`, `tidyr`, and `forcats` for data preparation;
* `lme4` and `lmerTest` for generalized and linear mixed-effects models;
* `emmeans` for planned contrasts and estimated marginal means;
* `DHARMa` for binomial GLMM diagnostics;
* `glmmTMB` for beta-family sensitivity analyses;
* `ggplot2` and `scales` for figures;
* `hmetad`, `brms`, `posterior`, and `bayesplot` for hierarchical meta-d analyses.

Install the required CRAN packages once:

```r
source("scripts/R/install_packages.R")
```

The project used `hmetad` version 0.1.2. This package is not installed automatically by `install_packages.R`; install the required version separately before running the scripts in `scripts/R/hmetad/`.

Run the main publication-oriented analyses:

```r
source("scripts/R/run_models_publication_v2.R")
```

Run the hierarchical meta-d analyses separately because they compile Stan models and may take several minutes:

```r
source("scripts/R/hmetad/01_fission_short_soa.R")
source("scripts/R/hmetad/02_congruent_baseline.R")
source("scripts/R/hmetad/03_context_comparison_short_soa.R")
source("scripts/R/hmetad/04_individual_mratio_associations.R")
```

The hierarchical meta-d scripts estimate:

* metacognitive efficiency in the short-SOA fission discrimination;
* metacognitive efficiency in the congruent baseline discrimination;
* the direct contextual comparison between physical and fission-related M-ratios;
* exploratory associations between individual M-ratio estimates and fission measures.

Other supplementary R scripts examine:

* changes in illusion rates across blocks;
* changes in confidence across blocks;
* participant-level response biases;
* correlations between physical two-flash reports and fission rates.

## Primary model formulas

```r
# Perceptual response
response2 ~ condition_cell + (1 | participant)

# Matched two-flash confidence
confidence ~ percept_origin * soa_type + (1 | participant)

# Matched one-flash confidence
confidence ~ fusion_comparison + (1 | participant)
```

The perceptual response model uses a binomial distribution with a logit link.

The confidence models use Gaussian linear mixed-effects models.

All primary effects are evaluated using likelihood-ratio tests comparing nested models. Planned contrasts are estimated with `emmeans`.

GLMM diagnostics use `DHARMa`. Confidence sensitivity analyses use beta-family models fitted with `glmmTMB`.

## Main manuscript outputs

Publication-oriented tables are written to:

```text
outputs/tables/results_v2/
```

The main manuscript figures are stored in:

```text
outputs/figures/perceptual/
outputs/figures/confidence/
```

The confidence directory intentionally contains only:

```text
03_confidence_composite_abcd.pdf
```

This is the confidence figure included in the submitted thesis.

Its active generation code is limited to:

```text
scripts/03_confidence_descriptives.py
src/confidence_figure.py
```

Older confidence figures and the code used only to produce them were removed from the repository.

## Hierarchical meta-d outputs

Selected tables and diagnostics from the hierarchical meta-d analyses are retained in directories such as:

```text
outputs/tables/hmetad_short/
outputs/tables/hmetad_congruent_baseline/
outputs/tables/hmetad_context_comparison_short/
outputs/tables/hmetad_individual_associations/
```

Large fitted model objects and trial-level exports are not included in the public repository.

The context-comparison model estimates M-ratios for:

```text
Physical context:
A1V1 versus A1V1_A2V2 short

Fission context:
A1V1_A2 short versus A1V1_A2V2 short
```

This comparison should be interpreted cautiously because the two contexts differ in their sensory structure and do not isolate percept origin alone.

## Reproducibility notes

The analysis code and selected derived outputs are retained in this repository. Participant-level input data are not distributed publicly, so the complete pipeline cannot be reproduced from the public repository alone.

With access to the original trial files, Python outputs can be regenerated by running:

```bash
python scripts/run_all.py
```

R outputs can be recreated by running the corresponding scripts from the repository root.

Stan-based hierarchical models may require several minutes to compile and fit. Their results may also depend on the installed versions of R, Stan, `brms`, and `hmetad`.

All scripts should be run from the repository root so that relative paths resolve correctly.

## Quality checks completed

* The Python pipeline was executed successfully on 5,184 trials from 9 participants.
* The original trial files remained unchanged during the analysis.
* Python source files compiled successfully.
* Generated cache directories were removed.
* Analysis scripts and technical comments were written in English.
* Manuscript-facing figure and table labels may remain in French.
* Confidence figures not used in the submitted thesis were removed.

The R analyses were not re-run during preparation of the public repository because R was unavailable in that environment. Existing derived outputs were retained.

## Reuse and responsibility

This repository was prepared as part of a Master's internship project.

No general permission for reuse, modification, or redistribution is granted by default because no software or data license is currently attached to the repository.

Any reuse of the code or data must comply with the study's ethical approval, participant consent, institutional policies, and the conditions agreed upon with the supervising laboratory.
