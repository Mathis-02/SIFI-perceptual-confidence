# ============================================================
# Install the R packages required by the SIFI analysis pipeline.
# Run once from the repository root.
# ============================================================

cran_packages <- c(
  "readr", "dplyr", "tibble", "tidyr", "forcats", "ggplot2", "scales",
  "lme4", "lmerTest", "emmeans", "pbkrtest", "glmmTMB", "DHARMa",
  "posterior", "bayesplot", "brms"
)

missing_cran <- cran_packages[
  !vapply(cran_packages, requireNamespace, logical(1), quietly = TRUE)
]

if (length(missing_cran) > 0) {
  install.packages(missing_cran, repos = "https://cloud.r-project.org")
}

if (!requireNamespace("hmetad", quietly = TRUE)) {
  message(
    "The hmetad package is not installed. This project used hmetad 0.1.2. Install the required version ",
    "according to the package documentation before running scripts in scripts/R/hmetad/."
  )
}

message("R package check completed.")
