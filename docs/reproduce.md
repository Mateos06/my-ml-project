# The tipping point

**NYC yellow taxis · Team D · May–July 2026**

A reproducible classification study of recorded card tips of at least 25% of the meter fare. The project goes from the instructor's fixed raw sample to a leakage-aware baseline, a locked July evaluation, and an evidence-driven MkDocs website.

## Start from a fresh clone

Requires Python 3.11 or 3.12 and Git. Run these commands from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
python -m pip install --no-deps -e .
python data/get_data.py
python -m pytest
python -m taxi_tip.cli develop
python -m taxi_tip.cli final --bootstrap 500
python -m taxi_tip.cli docs
python -m mkdocs build --strict
python -m mkdocs serve
```

On macOS/Linux activate with `source .venv/bin/activate`. The lock file records the tested Python 3.11 environment; its Windows terminal dependency has a platform marker. Alternatively install the compatible dependency ranges with `python -m pip install -e ".[dev,docs]"`.

Open <http://127.0.0.1:8000>. The static website is generated into `dist/`. Downloading the four files needs internet; subsequent analysis runs locally. Data, fitted models, environment files and row-level predictions are excluded from Git. The downloaded parquet and zone lookup are SHA-256 fingerprinted in the frozen result manifest.

The equivalent teaching route is `python -m jupyterlab`, then run `notebooks/01-frame.ipynb` through `04-evaluate.ipynb` in order. The notebooks import `src/taxi_tip`; they do not duplicate its implementation. Notebook 04 reuses a completed July result. To execute all notebooks automatically after the pipeline, use `python scripts/execute_notebooks.py`.

## What is in the repository

| Path | Purpose |
| --- | --- |
| `PROBLEM.md` | Target, population, prediction moment, costs and baseline contract |
| `data/get_data.py` | Instructor release downloader, safe extraction and checksums |
| `src/taxi_tip/` | Cleaning, feature pipelines, comparisons, evaluation and reports |
| `notebooks/01–04` | Four narrated stages with executable evidence |
| `reports/` | Measured aggregate tables, figures and frozen provenance |
| `MODEL_CARD.md` | Results, limits, intended use and failure slices |
| `docs/`, `mkdocs.yml` | Showcase website with results, reproducibility and presentation |
| `tests/` | Leakage, population, temporal split and holdout-guard checks |
| `presentation/DEFEND.md` | Fifteen-minute defense with speaker prompts |
| `PEER_REVIEW.md` | Honest pending review record and procedure |
| `.github/workflows/` | Automated tests and manual GitHub Pages deployment |

## July is a one-time test

`develop` reads only May and June and freezes hashes of the model, source, data and zone lookup. `final` verifies them, creates an exclusive `artifacts/july.lock`, scores July once, and caches the predictions before generating intervals. Repeat `final` calls return the saved result; `develop` refuses after the lock exists. There is no force flag.

If report generation is interrupted after predictions have been saved, rerun `final` to finish from the cache. If the process stopped before saving predictions, inspect the lock and failure, document any recovery, and acknowledge any prior July access. Do not delete the lock to tune against July. A fresh clone can reproduce the frozen method; that is replication, not a new holdout. Committed reports are evidence, and do not substitute for a local run's artifacts.

The trip-level paired bootstrap uses 500 resamples and fixed predictions. Its intervals omit model-selection uncertainty and may understate uncertainty from correlated trips. The study covers three months, not a full year.

## GitHub and the website

This directory is a Git repository. To connect it to an empty GitHub repository that you own:

```bash
git remote add github https://github.com/YOUR-ACCOUNT/YOUR-REPOSITORY.git
git push -u github HEAD:main
```

In GitHub Settings → Pages choose **GitHub Actions**, then run **Deploy MkDocs** under Actions. The deployment workflow builds the committed aggregate results; it never reopens July. For further commits use your chosen remote and branch. Do not upload `data/raw/` or `artifacts/`.

## Academic responsibility and AI use

OpenAI Codex assisted with the initial implementation, tests, documentation, figures, notebooks and presentation structure in this repository. Every team member must review the work, understand each line, verify the assumptions and be able to defend all stages. Do not claim these files were written manually or that the assistant's implementation is a substitute for understanding.

The peer review is **pending** until the Team A repository is supplied and actually reviewed. Team names, instructor access, submission deadline and the classroom defense remain human responsibilities. Commit history records actual work; it does not simulate four weeks of development.

Data source: the instructor's [data-v2 release](https://github.com/evisp/ml-course-labs/releases/tag/data-v2), based on [NYC TLC trip records](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page). See the website's sources and requirements pages for traceability.


## Download the four notebooks

1. [01 · Frame](downloads/01-frame.ipynb)
2. [02 · Clean and split](downloads/02-clean-and-split.ipynb)
3. [03 · Features](downloads/03-features.ipynb)
4. [04 · Evaluate](downloads/04-evaluate.ipynb)

Run these in the cloned project environment. They import the repository's source package.
