# Reproducibility

## Recommended order

1. Run `python scripts/run_all.py`.
2. Run `source("scripts/R/install_packages.R")` once.
3. Run `source("scripts/R/run_models_publication_v2.R")`.
4. Run the hierarchical meta-d scripts separately.
5. Compare regenerated tables and figures with the committed outputs.

## Random seeds

Bayesian scripts set explicit random seeds. Some exploratory scripts split or subsample trials and also set a seed. Do not change these seeds for exact regeneration.

## Software provenance

Record the output of:

```r
sessionInfo()
```

and:

```bash
python --version
pip freeze
```

when creating the final release tag.

## Known limitations

- Nine participants limit random-effects complexity and participant-level inference.
- Some hierarchical meta-d models can be weakly identified when error cells are sparse.
- The physical-versus-fission context comparison does not isolate percept origin because the S1 stimulus differs across contexts.
