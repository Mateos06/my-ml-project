# 🚕 The Tipping Point

### Can a taxi trip help predict a generous tip?

**600,000 NYC yellow-taxi records · May–July 2026 · Team D**

A reproducible machine-learning study that turns raw trip records into a validated baseline and an interactive visual story. We predict whether an eligible **card-paid trip receives a recorded tip of at least 25% of its meter fare**, at payment time, before the tip is entered.

**[↗ Explore the live website](https://nyc-taxi-tip-lab-mateo.violetnashi2.chatgpt.site)** · [Try the model](https://nyc-taxi-tip-lab-mateo.violetnashi2.chatgpt.site/#predictor) · [See the results](https://nyc-taxi-tip-lab-mateo.violetnashi2.chatgpt.site/#results)

![Animated study workflow: May trains on 129,956 eligible trips; June selects on 123,162; July tests the frozen model on 119,811. July average precision is 0.747 versus a 0.585 baseline.](docs/assets/readme/study-flow.gif)

*Follow the taxi from learning to validation to the final test. [View the still diagram](docs/assets/readme/study-flow.png) if you prefer no animation.*

## The result in 30 seconds

| July result | What it means |
| --- | --- |
| **0.747 average precision** | Better ranking than the constant-score baseline, **0.585**. AP is not accuracy. |
| **71.4% precision** | About 7 in 10 trips flagged as generous actually met the target. |
| **95.0% recall** | The model found about 95 in 100 trips that met the target. |
| **119,811 eligible trips** | The population behind the final test results. |

The selected **depth-eight decision tree** uses fare, geography and pre-tip fees. Its **0.32 decision threshold** was chosen on June and frozen before July. July AP has a **95% trip-bootstrap interval of 0.744–0.751**.

Three takeaways: trip context contains useful signal; cash tips are unobserved rather than zero generosity; even a useful model makes mistakes. This is an educational study of recorded card tips, not a judgment about passengers or a validated service-allocation tool.

## Explore the visual lab

- **Follow the evidence:** animated cleaning funnel, tip distributions and trip-pattern charts.
- **Explore New York:** real TLC taxi-zone boundaries, borough filters and sample-size context.
- **Look inside the models:** feature decisions, an interactive depth-two tree and model comparisons.
- **Test a trip:** run the actual frozen tree in your browser, with no trip inputs sent to a server.

Built with **Python · pandas · scikit-learn · MkDocs Material · Apache ECharts · JavaScript**. The site includes parallax, scroll animations, mobile layouts, reduced-motion support and accessible chart tables.

## Run the website locally

Requires **Python 3.11 or 3.12**; the dependency lock was tested on Python 3.11. From the repository root:

```bash
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

Then install and preview:

```bash
python -m pip install -r requirements-lock.txt
python -m pip install --no-deps -e .
python -m mkdocs serve
```

Open [localhost:8000](http://127.0.0.1:8000). Committed reports, browser model parameters and visual assets are included, so **previewing the site needs no raw-data download or model training**. Build static files into `dist/` with `python -m mkdocs build --strict`.

## How the study works

| Stage | Eligible card trips | Responsibility |
| --- | ---: | --- |
| **May → train** | 129,956 | Fit preprocessing and candidate models. |
| **June → select** | 123,162 | Choose feature groups, model and decision threshold. |
| **July → test once** | 119,811 | Evaluate the frozen choice and report uncertainty. |

The instructor sample contains 600,000 raw rows. Splits use recorded pickup timestamps; two rows fall in April and are excluded. All learned transformations fit on May only. Tip amount defines the target; **tip amount and total charge cannot enter the predictors**.

<details markdown="1">
<summary><strong>Reproduce the complete analysis</strong></summary>

After installing the environment above, use a fresh checkout with no existing study artifacts:

```bash
python data/get_data.py
python -m pytest
python -m taxi_tip.cli develop
python -m taxi_tip.cli final --bootstrap 500
python scripts/execute_notebooks.py
python -m taxi_tip.cli docs
python scripts/export_lab.py
node scripts/check_browser_model.cjs
python -m mkdocs build --strict
python scripts/check_site.py
```

Downloading the four instructor assets requires internet. Node.js is needed only for the browser/Python parity check. For the notebook route, download the data first, launch `python -m jupyterlab` and work through notebooks 01–04 in order; they import the shared Python package. Then run the documentation, export, parity and build commands above to refresh the website.

`develop` freezes source, model and data fingerprints. `final` creates `artifacts/july.lock`, scores July once and caches predictions. Subsequent `final` calls reuse the saved result; `develop` refuses after the lock exists. **Do not delete the lock to tune against July.** A fresh reproduction replicates the method; it does not create a new unseen test set.

If reporting stops after predictions were saved, rerun `final` to recover from the cache. If it stops before that point, inspect and document the failure and any previous July access before recovery.

Raw data, Python model binaries and row-level prediction caches stay outside Git. The website contains exported inference parameters, aggregates and two binned error examples. Browser exports use saved evaluation predictions without refitting or rescoring July.

</details>

## Repository guide

```text
data/get_data.py          Download the instructor's fixed sample
src/taxi_tip/            Cleaning, features, training, evaluation and reporting
notebooks/              Four executable stages: frame → clean → features → evaluate
reports/                Measured results, figures and frozen provenance
docs/                   MkDocs pages, browser code and visual assets
overrides/lab.html      Interactive homepage
scripts/                Exports, notebook execution and verification
tests/                  Leakage, split and holdout-guard checks
```

Start with the [problem and prediction contract](https://nyc-taxi-tip-lab-mateo.violetnashi2.chatgpt.site/problem/), [model card](https://nyc-taxi-tip-lab-mateo.violetnashi2.chatgpt.site/model-card/) or [15-minute defense](https://nyc-taxi-tip-lab-mateo.violetnashi2.chatgpt.site/presentation/). Their repository sources are `PROBLEM.md`, `MODEL_CARD.md` and `presentation/DEFEND.md`.

## Verification and limits

**Recorded checks:** 11 tests passed, the strict MkDocs build passed, and the JavaScript model matched scikit-learn on **1,000 May trips with zero probability difference**. Desktop and mobile interactions were checked. See `VALIDATION.md` for the verification record; these are completed local checks, not a claim about an unrun CI workflow.

The study covers eligible card payments in three months. Cash tips and human context are missing. The 500-resample trip bootstrap conditions on the fitted model, omits selection uncertainty and may understate uncertainty for correlated trips. June was reused for several choices. Read the [full evaluation](https://nyc-taxi-tip-lab-mateo.violetnashi2.chatgpt.site/evaluation/) before interpreting the headline numbers.

<details markdown="1">
<summary><strong>Publishing and visual maintenance</strong></summary>

The live showcase uses the URL above. The repository also includes a manual GitHub Pages workflow. To use your own empty GitHub repository:

```bash
git remote add github https://github.com/YOUR-ACCOUNT/YOUR-REPOSITORY.git
git push -u github HEAD:main
```

In **Settings → Pages**, select **GitHub Actions**, then run **Deploy MkDocs**. It builds committed results without reopening July. Do not upload `data/raw/` or `artifacts/`.

To rebuild the README animation, run `python scripts/render_readme_animation.py` (Pillow required). To restore pinned website photographs and ECharts assets, run `python scripts/fetch_lab_assets.py`. The custom MkDocs hook preserves the visual homepage when reports are regenerated.

</details>

## Sources, credits and academic responsibility

Data comes from the instructor's [data-v2 release](https://github.com/evisp/ml-course-labs/releases/tag/data-v2), based on [NYC TLC trip records](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page). [Visual credits and licenses](https://nyc-taxi-tip-lab-mateo.violetnashi2.chatgpt.site/lab-guide/) cover the photography and chart library. The README animation is a schematic of the study, not a recorded taxi route.

OpenAI Codex assisted with code, tests, notebooks, analysis presentation, documentation and website design. Team members must review, understand and defend the work. Peer review, classroom delivery and instructor submission remain pending human responsibilities; the repository does not claim those activities are complete.
