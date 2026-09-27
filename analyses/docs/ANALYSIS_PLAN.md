# Analysis plan

## Confirmatory analyses

### Perceptual reports
A binomial GLMM predicts the probability of a two-flash response from the experimental condition, with a participant random intercept. The condition-cell model is the manipulation check reported in the manuscript.

### Matched two-flash confidence
Trials are restricted to two-flash reports. A Gaussian LMM tests percept origin, SOA, and their interaction, with a participant random intercept.

### Matched one-flash confidence
Trials are restricted to one-flash reports. A Gaussian LMM compares congruent A1V1, standard-SOA fusion, and short-SOA fusion, with a participant random intercept.

### Inference
Fixed effects are tested with likelihood-ratio tests between nested maximum-likelihood models. Planned contrasts use estimated marginal means. The primary random-effects structure contains participant intercepts only because the sample contains nine participants; this is a stated limitation.

## Sensitivity analyses

- Beta mixed models for bounded confidence.
- One-inflated beta models for confidence values at 100%.
- DHARMa diagnostics for the perceptual GLMM.
- Residual diagnostics for Gaussian LMMs.

## Supplementary hierarchical meta-d analyses

- Short-SOA fission discrimination.
- Common-model comparison of physical and fission contexts.

These analyses estimate d-prime, meta-d-prime, decision criteria, confidence criteria, and M-ratio. The context comparison is informative but does not isolate percept origin perfectly because the S1 stimulus differs between contexts.

Historical outputs are retained for a congruent physical reference analysis, but its original implementation is no longer available. Its retained diagnostic report records 19 divergent NUTS transitions.

## Exploratory analyses

- Illusion-rate and confidence trajectories across blocks.
- Participant-level response-bias correlations.
- Associations between individual posterior M-ratios and fission outcomes.
- Leave-one-out sensitivity analyses for participant-level correlations.
