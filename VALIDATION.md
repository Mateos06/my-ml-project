# Validation record

Run on 3 November 2026, Windows, Python 3.11.9, scikit-learn 1.8.0.

- Downloaded the instructor's four data-v2 assets; parquet contains 600,000 rows and 21 columns.
- Audited pickup timestamps: April 2, May 199,999, June 200,001, July 199,998. The two April rows are outside the split.
- `python -m pytest`: 11 tests passed, including leakage, fit isolation, temporal boundaries, changed-fingerprint rejection, interrupted-score protection and cached final-result behavior.
- `python -m taxi_tip.cli develop`: fitted on May, compared on June, froze depth-eight tree with fare/geography/fees and threshold 0.32. A JSON serialization problem was fixed during development before July was opened; the development run then completed.
- `python -m taxi_tip.cli final --bootstrap 500`: completed one July scoring pass on 119,811 eligible trips. Cached predictions generated 500 paired bootstrap resamples.
- `python scripts/execute_notebooks.py`: all four notebooks executed with saved outputs. Notebook 04 reused the completed July result rather than scoring again.
- `python -m taxi_tip.cli docs` and `python -m mkdocs build --strict`: succeeded. An initial navigation configuration error was corrected before the successful build.
- Browser preview: homepage and evaluation pages rendered; the June threshold slider changed from 0.32 to 0.33 and updated false-positive/false-negative counts. The frozen model threshold was unchanged.

The dependency lock records the tested environment. A separate clean-machine installation and the GitHub-hosted Actions workflows have not been executed here. Peer review, team understanding, classroom delivery and instructor submission are not automated validation results.

## Interactive presentation — 7 November 2026

- Replaced the homepage with a responsive MkDocs template, concise three-insight overview, local photography, animated charts, scroll reveals, parallax, real taxi-zone map, model explanations and frozen-tree browser inference. Technical reports and notebook downloads remain available.
- `python -m pytest -q`: all 11 tests passed. `python -m mkdocs build --strict` succeeded.
- Export checks preserve the frozen Python source and artifact fingerprints. July curves and failures use existing predictions; no retraining or new July scoring took place.
- `node scripts/check_browser_model.cjs`: 1,000 May rows match sklearn exactly, with zero probability error and identical decisions. Forbidden and unused fields do not alter scores.
- Export audit: May histogram totals 129,956; all 102 June threshold matrices total 123,162; July metrics match the saved final report.
- Browser checks at desktop and 390-pixel mobile widths: target calculator, chart tabs, borough/zone selection, real tree, predictor, June threshold exploration, locked July threshold and navigation work. No horizontal page overflow was observed on mobile.
- Corrected an inherited theme-script error, mobile heading spacing, menu accessibility label and empty journey input validation. The final browser console reported no errors. Empty duration/distance display an actionable error; restoring valid values returns the expected 62.9% default estimate.
- Reduced-motion CSS/JavaScript fallbacks are implemented; OS-level reduced-motion emulation was not exercised in the browser.
- A local screenshot is saved in ignored `artifacts/redesigned-lab-preview.jpg`.
