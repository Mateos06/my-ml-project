"""Build an evidence-driven MkDocs showcase from aggregate saved reports."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
import pandas as pd

from .config import REPORTS, ROOT

DOCS = ROOT / "docs"


def md(table: pd.DataFrame, columns: list[str] | None = None) -> str:
    return (table[columns] if columns else table).to_markdown(index=False, floatfmt=".4f")


def read_table(name: str) -> pd.DataFrame:
    return pd.read_csv(REPORTS / "tables" / name)


def write(name: str, content: str):
    (DOCS / name).write_text(content.strip() + "\n", encoding="utf-8")


def build_docs():
    """No raw data, model loading, training, or holdout access occurs here."""
    selection = json.loads((REPORTS / "selection.json").read_text(encoding="utf-8"))
    final = json.loads((REPORTS / "final.json").read_text(encoding="utf-8"))
    validation = pd.read_csv(REPORTS / "validation_metrics.csv")
    test = pd.read_csv(REPORTS / "test_metrics.csv")
    intervals = read_table("bootstrap_intervals.csv")
    features = read_table("feature_comparison.csv")
    payments = read_table("payment_observability.csv")
    july = test.loc[test.model == "selected"].iloc[0]
    baseline = test.loc[test.model == "majority"].iloc[0]
    june = validation.loc[validation.model == selection["selected_model"]].iloc[0]
    ap_interval = intervals.loc[(intervals.metric == "average_precision") & (intervals.estimator == "model")].iloc[0]
    gain = float(july.average_precision - baseline.average_precision)
    improvement = float(baseline.cost_per_trip - july.cost_per_trip)
    failures = read_table("test_slices.csv")
    failures = failures.loc[failures.n >= 200].sort_values("cost_per_trip", ascending=False).head(8)
    dropped = features.loc[~features.retained.astype(bool), "addition"].tolist()
    losers = ", ".join(dropped) if dropped else "none of the tested additions"
    cols = ["model", "n", "average_precision", "precision", "recall", "lift_at_20pct", "cost_per_trip", "threshold"]
    (DOCS / "assets" / "figures").mkdir(parents=True, exist_ok=True)
    downloads = DOCS / "downloads"
    downloads.mkdir(exist_ok=True)
    for path in (REPORTS / "figures").glob("*.png"):
        shutil.copy2(path, DOCS / "assets" / "figures" / path.name)
    for path in [*REPORTS.glob("*.csv"), *(REPORTS / "tables").glob("*.csv"), *REPORTS.glob("*.json")]:
        shutil.copy2(path, downloads / path.name)
    shutil.copy2(REPORTS / "depth2_rules.txt", downloads / "depth2_rules.txt")
    for path in (ROOT / "notebooks").glob("*.ipynb"):
        shutil.copy2(path, downloads / path.name)
    costs = read_table("validation_thresholds.csv")
    (DOCS / "assets" / "thresholds.json").write_text(costs.iloc[:101].to_json(orient="records"), encoding="utf-8")
    raw_counts = read_table("pickup_month_audit.csv")
    total_raw = int(raw_counts.n.sum())

    write("index.md", f'''
---
hide:
  - toc
---
<section class="hero">
<svg class="hero-line" viewBox="0 0 240 240" aria-hidden="true"><path d="M10 220V120H70V40H140V180H210V10M0 70H230M0 145H230M40 0V240M180 0V240"/></svg>
<div class="eyebrow">Project 01 / Team D / New York City</div>
<h1>The tipping point.</h1>
<p class="lead">A trip ends. The payment screen opens.<br>How much can the journey tell us about a generous tip?</p>
<p>From {total_raw:,} raw taxi records to one held-out result. A transparent study of what simple models can—and cannot—learn about recorded card tips.</p>
<a class="button" href="evaluation/">Explore the results →</a>
<a class="button secondary" href="reproduce/">Reproduce the study</a>
<div class="study-meta"><span><strong>25% of fare</strong>Our positive target</span><span><strong>May → June → July</strong>Fit · choose · test</span><span><strong>{selection['selected_model'].replace('_', ' ')}</strong>Chosen on June</span></div>
</section>

<div class="metric-grid">
<div class="metric"><div class="value">{july.average_precision:.3f}</div><div class="label">July average precision</div><div class="detail">95% CI {ap_interval.lower_95:.3f}–{ap_interval.upper_95:.3f}</div></div>
<div class="metric"><div class="value">{baseline.average_precision:.3f}</div><div class="label">Constant-score baseline AP</div><div class="detail">July positive prevalence</div></div>
<div class="metric"><div class="value">{july.lift_at_20pct:.2f}×</div><div class="label">Lift in the top 20%</div><div class="detail">Compared with the July population</div></div>
<div class="metric"><div class="value">{int(july.n):,}</div><div class="label">Eligible July card trips</div><div class="detail">One frozen scoring pass</div></div>
</div>

<div class="verdict"><strong>The measured result</strong><br>The selected model changes average precision by {gain:+.3f} versus the constant-score baseline. At the June-selected threshold, July precision is {july.precision:.1%} and recall is {july.recall:.1%}. These are limits of this study, not a claim that a trip record can reveal a person's generosity.</div>

## First, ask a question the data can answer

Cash tips are absent from the meter record. Treating those zeros as failed generosity would teach a model about payment recording. We ask a narrower question: **among eligible card trips, is the recorded tip at least 25% of the fare?**

<div class="evidence-pair"><article><div class="eyebrow">01 / Define the population</div><h3>Missing is not ungenerous.</h3><p>The payment audit makes the cash problem visible. Every removal has a count and a remaining positive rate.</p><a href="data/">Inspect the cleaning evidence →</a></article><article><div class="eyebrow">02 / Respect the clock</div><h3>The tip stays outside the model.</h3><p>Distance and duration are known at payment. The tip and total charge are not usable predictors.</p><a href="features/">Inspect the feature decisions →</a></article></div>

## Three months, three different jobs

<div class="stage-strip"><div><b>May · fit</b><span>{selection['n_train']:,} eligible trips<br>All learned preprocessing and models</span></div><div><b>June · choose</b><span>{selection['n_validation']:,} eligible trips<br>Features, model, threshold</span></div><div class="held-out"><b>July · test once</b><span>{final['n_test']:,} eligible trips<br>Frozen predictions and intervals</span></div></div>

![July precision–recall and reliability plots](assets/figures/july-performance.png)

Read the [model card](model-card.md) for failure slices and limits, or use the [15-minute defense](presentation.md) to walk through the evidence. The [peer review](peer-review.md) remains pending until Team A's repository is available.

<p class="source-note">Measured from the instructor's fixed data-v2 sample. Aggregate reports and figures are generated by Python. No demonstration metrics are presented as real results.</p>
''')
    write("problem.md", (ROOT / "PROBLEM.md").read_text(encoding="utf-8"))
    audit = read_table("cleaning_train.csv")
    clean_columns = ["step", "decision", "remaining", "removed", "card_positive_rate"]
    write("data.md", f'''
# From raw records to an observable target

The instructor release contains **{total_raw:,} rows** with 21 columns. We preserve the source and checksum it; cleaning rebuilds from raw files on every independent run.

## The timestamp audit

{md(raw_counts)}

Counts follow recorded pickup timestamps, not an assumption of exactly 200,000 rows per calendar month. Rows outside May–July are excluded by the temporal read filters. This structural audit reads only pickup timestamps; July outcomes remain unopened until final evaluation.

## The cash leak, made visible

{md(payments)}

These are **recorded** rates, not true tip rates for non-card payments. A cash zero is a missing cash-tip measurement. Including cash as a negative class creates an observability shortcut through payment type and its proxies. It does not show that cash passengers are less generous. The production feature allowlist excludes payment type after using it to select card trips.

![Recorded tip rates by payment type](assets/figures/payment-observability.png)

## Every cleaning decision has a count

The table is May only. Its positive-rate denominator is the remaining card trips with a valid fare and tip, even before the card-only filter. It never assigns negative labels to cash trips.

{md(audit, clean_columns)}

[May audit](downloads/cleaning_train.csv) · [June audit](downloads/cleaning_validation.csv) · [July audit](downloads/cleaning_test.csv)

[Raw-column missingness and negative-value audit](downloads/raw_column_audit.csv) · [Retained flags with counts](downloads/retained_flags.csv)

Unknown zones are retained as category 265 and flagged; missing, zero or invalid passenger counts become an explicit unknown category. Nonstandard fares remain with their rate codes and a flag. Flex fares are excluded because the target is defined for card trips, not because missing metadata alone makes a trip invalid. Negative fare, tip or component fees are dropped; we do not flip their signs. Total amount is audited but never used for eligibility, features or target construction because it already includes the outcome. Fixed journey limits may remove some unusual legitimate trips, so conclusions apply to the eligible population.

## What the tip distribution tells us

![May tip percentage distribution](assets/figures/tip-distribution.png)

Peaks and round percentages are consistent with people using customary amounts or payment-screen presets. The record does not contain the screen choices, so it cannot prove that mechanism. Fare-only percentages may also differ from presets calculated on a larger pre-tip charge. Values above 100% are retained in modeling and pooled only in the final histogram bin.

## Differences that might matter

These are May associations, with Wilson 95% intervals and sample sizes. A difference of at least five percentage points from the May population rate is labelled practically large, before considering uncertainty. This is descriptive screening, without multiple-comparison correction or a causal interpretation.

![May hourly tip rates and intervals](assets/figures/hour-rates.png)

{md(read_table('rates_airport_trip.csv'))}

{md(read_table('rates_fare_band.csv'))}

Full tables: [distance](downloads/rates_distance_band.csv), [duration](downloads/rates_duration_band.csv), [hour](downloads/rates_pickup_hour.csv), [day of week](downloads/rates_day_of_week.csv), [passengers](downloads/rates_passenger_count.csv), [borough](downloads/rates_pickup_borough.csv), [nonstandard rates](downloads/rates_nonstandard_rate.csv). Day 0 is Monday; airport 1 means pickup or drop-off is EWR, JFK or LGA.

## Geography, without false precision

![May generous tip rates by pickup zone](assets/figures/zone-rates.png)

The map uses the supplied shapefile's native projected coordinates in feet, with no latitude/longitude claim. Zones with fewer than 200 eligible May trips are uncolored. Zone-only data cannot locate a rider or resolve within-zone differences.
''')
    feature_descriptions = pd.DataFrame([
        ["fare", "Meter fare", "Known at payment; numeric"],
        ["journey", "Duration, distance, average speed", "Derived from completed trip"],
        ["calendar", "Hour, cyclic hour, day of week", "Known pickup timestamp; no month feature"],
        ["geography", "Pickup/drop-off zones, borough, airport", "Categorical zones; no false numeric ordering"],
        ["passengers", "Passenger count", "Categorical; unknown retained"],
        ["rate", "Rate code", "Known at end of trip"],
        ["fees", "Seven pre-tip surcharges/fees", "Numeric; median imputation learned in May"],
        ["quality", "Unknown zone, rate and passenger flags", "Fixed deterministic rules"],
    ], columns=["Group", "Features", "Reason available"])
    write("features.md", f'''
# Every addition earns its place on June

The pipeline fits numeric median imputation, standard scaling and categorical one-hot encoding **on May only**. Unknown categories at prediction time are handled without refitting. An explicit allowlist drops all other columns, including tip, total charge and the target.

{md(feature_descriptions)}

Vendor ID, store-and-forward flag and request source are deliberately not candidates: this small study prioritizes interpretable trip information and avoids relying on provider or recording-system proxies. Tip percentage, tip amount, total amount, target and payment type are forbidden. Exclusion by design is distinct from losing an empirical feature comparison.

## The feature ledger

Starting with fare, test groups in the stated order with logistic regression; retain an addition only if June AP improves by at least 0.001. Later groups build on the retained set. This is an order-dependent, greedy comparison, not an exhaustive test of all interactions or separate leave-one-feature-out effects. Tree models share this selected representation; a tree-specific selection could produce a different result.

{md(features)}

**Rejected additions:** {losers}. Rejection means the feature group did not meet this procedure's June improvement rule; it does not establish that it has no information.

## The baseline ladder and model comparison

The May-derived rule selects fare band **{selection['fare_rule']['band']}**. A majority decision uses a 0.5 threshold on constant May prevalence; a majority baseline can therefore have zero recall. The depth-two tree is the final rung of the simple baseline ladder. Each learned model has its own cost-minimizing June threshold.

{md(validation, cols)}

**Selected: {selection['selected_model']}**, using {', '.join(selection['feature_groups'])}. Ranking uses June AP; the operating threshold is a separate cost decision. June AP is a development score after multiple choices, not an unbiased estimate of future performance.

[Download the feature ledger](downloads/feature_comparison.csv) · [Download the complete June table](downloads/validation_metrics.csv)

## Read the two-level tree

```text
{(REPORTS / 'depth2_rules.txt').read_text(encoding='utf-8')}
```

The numeric thresholds shown here are standardized by the May-fitted scaler. They are not raw dollar amounts. The root and its immediate child splits are the two decision levels.

## Leakage tests

Tests perturb every forbidden column and verify predictions remain identical, pass unseen zones and extreme validation values without changing fitted imputer statistics, check exact temporal boundaries, and exercise both the post-July development refusal and cached-result path. Numeric thresholds in cleaning are constants, not quantiles estimated from the combined months.
''')
    write("evaluation.md", f'''
# One final look at July

Features, model and threshold were selected on June before opening July outcomes. The July evaluator verifies frozen SHA-256 hashes, creates an exclusive lock, saves one prediction pass, and calculates reports from that cache. There is no automatic retry that silently scores the holdout again.

## What survived the month change

{md(test, cols)}

The selected model's AP changes from **{june.average_precision:.4f} in June** to **{july.average_precision:.4f} in July**. Constant-score AP equals the July positive prevalence. Average precision is non-interpolated PR AUC; it is not trapezoidal area and not accuracy.

![July PR and reliability](assets/figures/july-performance.png)

## Uncertainty beside the baseline

{md(intervals)}

**{final['bootstrap_repetitions']} paired bootstrap resamples**, trip-level, seed 2026, percentile 95% intervals. Each resample uses the same indices for model and majority; the difference rows are paired model-minus-baseline contrasts. A negative cost difference is better. Predictions stay fixed throughout. Correlated trips and model-selection uncertainty are not represented; these are conditional intervals for this evaluation sample, not guarantees about future months.

## A decision threshold with a stated price

We assign a false positive 1 cost unit and a false negative 2. The June-selected threshold is **{selection['threshold']:.2f}**, with July cost **{july.cost_per_trip:.4f}** per trip versus majority cost **{baseline.cost_per_trip:.4f}**. The reduction is **{improvement:.4f}** cost units per trip under those assumed costs. No dollars or operational benefit have been measured.

<div class="explorer" data-threshold-explorer data-source="../assets/thresholds.json">
<label for="threshold">Explore the June decision curve · threshold <b data-value>{selection['threshold']:.2f}</b></label>
<input id="threshold" type="range" min="0" max="100" value="{min(100, round(selection['threshold'] * 100))}" aria-label="June decision threshold">
<div class="explorer-output"><span><strong data-cost>—</strong>Cost per trip</span><span><strong data-fp>—</strong>False positives</span><span><strong data-fn>—</strong>False negatives</span></div>
<p class="source-note" data-status>Read-only exploration of June. This control never changes the frozen threshold or scores July.</p>
</div>

![June threshold versus cost](assets/figures/threshold-cost.png)

## Reliability, not just ranking

![June precision–recall and reliability](assets/figures/june-performance.png)

July Brier score is **{july.brier:.4f}**, versus **{baseline.brier:.4f}** for constant May prevalence. Reliability tables contain counts, mean predicted probability and observed positive rate in fixed 0.1 bins; empty bins are omitted. No post-hoc calibration is fitted, and small bins should not be overinterpreted.

[June reliability](downloads/validation_reliability.csv) · [July reliability](downloads/test_reliability.csv)

## Where the model is least useful

The eight highest-cost slices with at least 200 eligible July trips are below. Slices overlap, so counts must not be added together. Selection of these slices is descriptive after testing, not a basis for retuning the model.

{md(failures, ['slice', 'value', 'n', 'positive_rate', 'average_precision', 'precision', 'recall', 'cost_per_trip'])}

The [full July slice table](downloads/test_slices.csv) includes every slice, counts and a small-sample flag. [June slices](downloads/validation_slices.csv) were available during development. Unknown passenger values are labelled `nan` in exported tables.

[Download July metrics](downloads/test_metrics.csv) · [Paired intervals](downloads/bootstrap_intervals.csv) · [Frozen provenance](downloads/final.json)
''')
    model_card = f'''
# Model card · generous card-tip baseline

## Intended use and exclusions

An educational, retrospective driver-support study of NYC yellow-taxi trips at payment time. Positive means a recorded card tip at least 25% of positive meter fare. This model is not validated for decisions about service access, routing, pricing, worker evaluation or individual passenger treatment. There is no deployment recommendation.

Cash, flex, no-charge, disputed, unknown-payment and voided trips are outside the population. All findings are conditional on our fixed cleaning rules and observed card trips; neither zeros in cash records nor missing tips establish human generosity.

## Data, fitting and provenance

Instructor data-v2 fixed sample, May–July 2026. Eligible rows: May **{selection['n_train']:,}**, June **{selection['n_validation']:,}**, July **{final['n_test']:,}**. Pickup month defines the split. The selected estimator is **{selection['selected_model']}**, fitted on May only with groups **{', '.join(selection['feature_groups'])}**. Model and threshold choices use June; no refit combines May and June.

Trip file SHA-256: `{selection['data_sha256']}`.

Model SHA-256: `{selection['model_sha256']}`.

The source fingerprint, Python/scikit-learn versions, seed and complete decision record are in `reports/selection.json`. July's result and prediction fingerprints are in `reports/final.json`. Row-level data and models remain local and are not in the website.

## Measured performance

{md(test, cols)}

July AP: **{july.average_precision:.4f}**, 95% trip-bootstrap interval **[{ap_interval.lower_95:.4f}, {ap_interval.upper_95:.4f}]**; constant-score baseline AP **{baseline.average_precision:.4f}**. AP lift over baseline is **{gain:+.4f}**. July top-20% lift is **{july.lift_at_20pct:.3f}**. July Brier score is **{july.brier:.4f}**. These results measure the tested model family, not the theoretical ceiling of tipping prediction.

At threshold **{selection['threshold']:.2f}**, precision is **{july.precision:.1%}**, recall **{july.recall:.1%}**, and **{july.predicted_positive_rate:.1%}** of eligible trips are flagged. False-positive cost is 1 and false-negative cost is 2 hypothetical units; the assumption needs stakeholder validation. July cost is **{july.cost_per_trip:.4f}** versus **{baseline.cost_per_trip:.4f}** for majority.

## Where it fails and why caution is necessary

{md(failures, ['slice', 'value', 'n', 'precision', 'recall', 'cost_per_trip'])}

These overlapping slices are the highest-cost groups with n ≥ 200; the full slice report includes smaller groups. A useful aggregate ranking does not imply useful predictions in every group. Zones, fare and time describe trip context rather than intent, service quality, rider income or satisfaction. None of those missing concepts can be inferred as causal explanations.

There is only one held-out month. Seasonal shifts, future fares, recording changes and different payment interfaces can change performance. June was reused for feature/model/threshold choices, which makes development scores optimistic. Greedy feature selection is order dependent and uses logistic regression for all candidate groups. Rejected groups: **{losers}**.

No post-hoc calibration was fitted. The reliability diagram and Brier score are diagnostics; predicted probabilities should not be treated as guaranteed individual frequencies. The {final['bootstrap_repetitions']}-resample paired bootstrap conditions on fixed predictions and treats trips as independent; it omits selection uncertainty and may understate uncertainty for correlated trips. No causal, fairness, economic-impact or full-year validation has been performed.

## Reproduction and governance

Run the README from a fresh clone. A local exclusive July lock prevents accidental repeat tuning; cached predictions support report recovery. This guard can be bypassed by manual file deletion, so research discipline and the recorded provenance remain necessary. Independent reruns of the same fixed method are replication, not fresh tests.

AI assistance is declared in the README. Team members must understand and verify the work. Peer review and classroom defense remain pending human activities. Future changes must be evaluated on a new, genuinely unseen period; do not optimize against this July result.
'''
    (ROOT / "MODEL_CARD.md").write_text(model_card.strip()+"\n", encoding="utf-8")
    write("model-card.md", model_card)
    write("reproduce.md", (ROOT / "README.md").read_text(encoding="utf-8") + '''

## Download the four notebooks

1. [01 · Frame](downloads/01-frame.ipynb)
2. [02 · Clean and split](downloads/02-clean-and-split.ipynb)
3. [03 · Features](downloads/03-features.ipynb)
4. [04 · Evaluate](downloads/04-evaluate.ipynb)

Run these in the cloned project environment. They import the repository's source package.
''')
    presentation = f'''
# The tipping point · 15-minute defense

Use each numbered section as a speaking segment. Open the linked website figures alongside this outline. Every member should be able to explain every segment; fill in the actual speaker names before class.

## 1. One question, one moment · 0:00–1:30

At payment time, will an eligible card trip have a recorded tip of at least 25% of meter fare? Explain why distance is available now and total amount is not. Establish that this is prediction of a recorded outcome, not a character judgment.

**Show:** target and payment-time feature contract.

## 2. The decision we stand behind · 1:30–3:30

Explain why a cash zero is not a negative example. Show the May payment-type table and card-only population. Explain flex fares, voided/disputed trips, positive fares, fixed plausibility limits, and retained unknown zones/nonstandard rates. Point to the attrition counts rather than only listing rules.

**Show:** payment-observability and cleaning tables.

## 3. What the raw patterns suggest · 3:30–5:00

Show the tip-percentage distribution, hourly uncertainty bands, fare/airport effect sizes and the zone map. Peaks are consistent with common choices; the records do not identify the mechanism. Explain why native shapefile feet are not latitude/longitude.

## 4. Three months, three jobs · 5:00–6:30

May fits all transformations and models; June decides; July is opened once. Explain that timestamp filters handle the actual dates instead of forcing three arbitrary blocks of 200,000. Demonstrate the source/data/model fingerprint and holdout lock.

## 5. The ladder and what did not help · 6:30–8:30

Walk from majority to May fare-band rule to depth-two tree to logistic regression/deeper single trees. Rejected feature additions: **{losers}**. Explain the 0.001 June AP gate, greedy order and shared representation. Selected model: **{selection['selected_model']}**.

## 6. The result and its price · 8:30–11:00

July AP **{july.average_precision:.3f}** with 95% interval **{ap_interval.lower_95:.3f}–{ap_interval.upper_95:.3f}**, versus baseline **{baseline.average_precision:.3f}**. Precision **{july.precision:.1%}**, recall **{july.recall:.1%}**, top-20% lift **{july.lift_at_20pct:.2f}×**. Explain AP versus accuracy and paired bootstrap differences. Threshold **{selection['threshold']:.2f}** follows FP=1, FN=2 assumed costs, not a default 0.5.

## 7. Where it fails · 11:00–13:00

Use the highest-cost slices in the model card, with their counts. Explain calibration, absent rider/service information, cash exclusion, seasonal uncertainty and correlated trips. A modest score can be an honest limit of these baselines; it cannot establish the irreducible ceiling.

## 8. Reproduce, challenge, conclude · 13:00–15:00

Show the fresh-clone commands, tests, four notebooks and committed aggregate outputs. Declare AI assistance. State the peer review status truthfully. Invite questions on one cleaning boundary, one rejected feature, one cost assumption and one failure slice.

## Questions every member should rehearse

- Why is a 25% tip on fare different from 25% of total charge?
- Can the model ever see tip or total amount? Show the allowlist and leakage test.
- What does the majority baseline's AP mean if its recall is zero?
- Why does a higher AP not guarantee lower cost at every threshold?
- What is the bootstrap sampling unit, and what uncertainty does it miss?
- What would you do if July looked worse? Report it; obtain a new holdout for future work.
- Which choices are fixed judgment calls and which were learned on May or selected on June?
'''
    (ROOT / "presentation").mkdir(exist_ok=True)
    (ROOT / "presentation" / "DEFEND.md").write_text(presentation.strip()+"\n", encoding="utf-8")
    write("presentation.md", presentation)
    write("peer-review.md", (ROOT / "PEER_REVIEW.md").read_text(encoding="utf-8"))
    write("requirements.md", '''
# Requirement traceability

| Brief requirement | Evidence | Status |
| --- | --- | --- |
| Precise target and prediction moment | Problem card, notebook 01 | Implemented |
| Target decisions and positive rates | Ordered cleaning audit, notebook 02 | Measured |
| Cash-tip observability demonstration | Payment-type table and chart | Measured |
| Flex, invalid trips, unknown zones, nonstandard rates | Cleaning policy and attrition tables | Implemented |
| Tip distribution and substantive slice effects | Histogram, Wilson intervals, rate tables, zone map | Measured |
| May training, June decisions, July one final evaluation | Temporal reads, fingerprints, exclusive lock | Implemented |
| Majority, rule, depth-two tree | June and July comparison tables | Measured |
| Logistic regression and a single decision tree | June candidate comparison | Measured |
| Each candidate feature judged on June; losses retained | Feature-group ledger with negative/insufficient gains | Measured |
| Learned transformations fit on May | scikit-learn pipeline and leakage tests | Verified by tests |
| Precision, recall, PR AUC, lift | June/July metrics and slice CSVs | Measured |
| Cost threshold and reliability check | June cost explorer, reliability plots and Brier score | Measured |
| July bootstrap beside baseline | Paired intervals and differences | Measured |
| Four notebooks importing reusable source | Downloadable notebooks and src/taxi_tip | Implemented |
| README, problem card, model card | Repository and mirrored website pages | Written |
| Fifteen-minute presentation | Defense outline with timings and measured results | Prepared; delivery pending |
| Useful peer review, delivered to Team A | Peer review record | Pending: Team A repository needed |
| Git history, GitHub access and submission | Local repository and deployment workflow | Local history created; instructor submission pending |
| AI disclosure and team understanding | README disclosure, rehearsal questions | Disclosed; human review/understanding required |

The project does not claim a peer review, classroom presentation, instructor submission or human understanding that has not occurred.
''')
    write("sources.md", '''
# Sources and metric definitions

- [Instructor fixed-sample release, data-v2](https://github.com/evisp/ml-course-labs/releases/tag/data-v2). The downloader uses exactly this release; SHA-256 hashes identify the files used.
- [NYC TLC trip-record data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page). Dataset context and official download reference. TLC cautions that provider-supplied trip records can contain inaccuracies.
- [Official yellow-taxi data dictionary](https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf). Field and code meanings, including the scope of recorded tips. The instructor's copy is also downloaded locally.
- [Scikit-learn average precision](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html). The primary metric is non-interpolated AP, not trapezoidal PR area.
- [Scikit-learn pitfalls and data leakage](https://scikit-learn.org/stable/common_pitfalls.html). Pipelines keep fitted preprocessing in the training process.
- [MkDocs deployment guide](https://www.mkdocs.org/user-guide/deploying-your-docs/). The website builds to static assets; GitHub Pages can host them.

The supplied project brief defines the academic task and target. Our fixed cleaning cutoffs, practical-effect marker, candidate model grid and cost assumptions are project decisions, not official TLC rules. All reported metric values come from this repository's saved computations rather than external publications.
''')
    print("Generated MkDocs pages, model card and defense outline from saved aggregates.")
