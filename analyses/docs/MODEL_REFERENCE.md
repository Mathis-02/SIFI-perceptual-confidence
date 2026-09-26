# Model reference

| Analysis | Model | R package/function |
|---|---|---|
| Two-flash perceptual response | Binomial GLMM with logit link | `lme4::glmer` |
| Matched two-flash confidence | Gaussian LMM | `lme4::lmer`, `lmerTest` |
| Matched one-flash confidence | Gaussian LMM | `lme4::lmer`, `lmerTest` |
| Planned contrasts | Estimated marginal means | `emmeans` |
| GLMM diagnostics | Simulation-based residuals | `DHARMa` |
| Beta confidence sensitivity | Beta GLMM | `glmmTMB::glmmTMB` |
| One-inflated confidence sensitivity | Inflated beta mixed model | `glmmTMB` |
| Hierarchical meta-d | Bayesian multilevel SDT model | `hmetad`, `brms`, Stan |
| Participant correlations | Spearman/Pearson tests | `stats::cor.test` |
| Figures | Publication and diagnostic plots | `ggplot2`, Python `matplotlib` |

Primary likelihood-ratio tests use `anova(reduced_model, full_model, test = "Chisq")` for nested models fitted by maximum likelihood.
