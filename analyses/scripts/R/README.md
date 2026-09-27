# R analysis scripts

## Primary and sensitivity analyses

| Script | Role |
|---|---|
| `install_packages.R` | Check and install required R packages |
| `run_models_publication_v2.R` | Primary mixed models, planned contrasts, diagnostics, and manuscript tables |
| `sensitivity_one_inflated_beta_confidence.R` | Bounded-confidence sensitivity analyses |
| `09_illusion_rates_by_block.R` | Exploratory block trajectories and GLMMs for illusion rates |
| `10_confidence_by_block.R` | Exploratory block trajectories and LMMs for illusory confidence |
| `11_response2_physical_fission_correlation.R` | Physical two-flash reporting versus fission |
| `12_baseline_response_bias_fission_correlation.R` | Baseline response bias versus fission |

## HMeta-d analyses

All HMeta-d scripts are grouped in [`hmetad/`](hmetad/):

| Script | Role |
|---|---|
| `hmetad/01_fission_short_soa.R` | Short-SOA fission HMeta-d |
| `hmetad/02_congruent_baseline.R` | Historical congruent reference; original implementation unavailable |
| `hmetad/03_context_comparison_short_soa.R` | Direct context comparison in one hierarchical model |
| `hmetad/04_individual_mratio_associations.R` | Individual M-ratio associations and leave-one-out checks |

The block, correlation, and individual-association analyses are exploratory and should not be described as confirmatory.
