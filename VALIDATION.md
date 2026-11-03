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
