# Hierarchical meta-d analyses

These scripts contain all HMeta-d and individual M-ratio analyses used in the project. Run them from the repository root.

| Script | Analysis |
|---|---|
| `01_fission_short_soa.R` | HMeta-d for the short-SOA fission versus congruent discrimination |
| `02_congruent_baseline.R` | Congruent reference HMeta-d using A1V1 versus short-SOA A1V1_A2V2 |
| `03_context_comparison_short_soa.R` | Single hierarchical model directly comparing physical and fission contexts at the short SOA |
| `04_individual_mratio_associations.R` | Exploratory associations between individual posterior M-ratios and fission outcomes |

The context-comparison model is the most direct supplementary test. It estimates a context effect on log M-ratio in one model. The two contexts still differ in physical stimulus structure, so the effect cannot be interpreted as a pure readout of percept origin.
