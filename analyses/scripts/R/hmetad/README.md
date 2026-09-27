# Hierarchical meta-d analyses

These scripts contain the HMeta-d and individual M-ratio analyses used in the project. Run them from the `analyses/` directory.

| Script | Analysis |
|---|---|
| `01_fission_short_soa.R` | HMeta-d for the short-SOA fission versus congruent discrimination |
| `02_congruent_baseline.R` | Placeholder documenting a historical congruent-reference analysis whose original implementation is no longer available |
| `03_context_comparison_short_soa.R` | Single hierarchical model directly comparing physical and fission contexts at the short SOA |
| `04_individual_mratio_associations.R` | Exploratory associations requiring the retained congruent-baseline fitted model, which is not distributed publicly |


The retained congruent-baseline outputs come from an analysis that was run during the project, but its original implementation is not available in this repository. Its diagnostic report records 19 divergent NUTS transitions despite satisfactory R-hat and effective sample-size values. These outputs are retained for transparency rather than presented as a fully reproducible analysis.

The context-comparison model is the most direct supplementary test. It estimates a context effect on log M-ratio in one model. The two contexts still differ in physical stimulus structure, so the effect cannot be interpreted as a pure readout of percept origin.
