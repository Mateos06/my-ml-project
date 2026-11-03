# Model card · generous card-tip baseline

## Intended use and exclusions

An educational, retrospective driver-support study of NYC yellow-taxi trips at payment time. Positive means a recorded card tip at least 25% of positive meter fare. This model is not validated for decisions about service access, routing, pricing, worker evaluation or individual passenger treatment. There is no deployment recommendation.

Cash, flex, no-charge, disputed, unknown-payment and voided trips are outside the population. All findings are conditional on our fixed cleaning rules and observed card trips; neither zeros in cash records nor missing tips establish human generosity.

## Data, fitting and provenance

Instructor data-v2 fixed sample, May–July 2026. Eligible rows: May **129,956**, June **123,162**, July **119,811**. Pickup month defines the split. The selected estimator is **tree_depth_8**, fitted on May only with groups **fare, geography, fees**. Model and threshold choices use June; no refit combines May and June.

Trip file SHA-256: `9f6fadc8308f30f194e9980a170aceadb9e2114e50c1d5d0b574ab82a07c5af0`.

Model SHA-256: `94a8feaa3db92f1467a26c5339853337f4cd19e0320ebd717e98ed2c99fd42ce`.

The source fingerprint, Python/scikit-learn versions, seed and complete decision record are in `reports/selection.json`. July's result and prediction fingerprints are in `reports/final.json`. Row-level data and models remain local and are not in the website.

## Measured performance

| model        |      n |   average_precision |   precision |   recall |   lift_at_20pct |   cost_per_trip |   threshold |
|:-------------|-------:|--------------------:|------------:|---------:|----------------:|----------------:|------------:|
| majority     | 119811 |              0.5845 |      0.5845 |   1.0000 |          1.0000 |          0.4155 |      0.5000 |
| fare_rule    | 119811 |              0.6564 |      0.7573 |   0.4163 |          1.2955 |          0.7604 |      0.7614 |
| tree_depth_2 | 119811 |              0.7063 |      0.6440 |   0.9742 |          1.2323 |          0.3450 |      0.3900 |
| selected     | 119811 |              0.7474 |      0.7137 |   0.9497 |          1.3279 |          0.2815 |      0.3200 |

July AP: **0.7474**, 95% trip-bootstrap interval **[0.7437, 0.7508]**; constant-score baseline AP **0.5845**. AP lift over baseline is **+0.1629**. July top-20% lift is **1.328**. July Brier score is **0.1821**. These results measure the tested model family, not the theoretical ceiling of tipping prediction.

At threshold **0.32**, precision is **71.4%**, recall **95.0%**, and **77.8%** of eligible trips are flagged. False-positive cost is 1 and false-negative cost is 2 hypothetical units; the assumption needs stakeholder validation. July cost is **0.2815** versus **0.4155** for majority.

## Where it fails and why caution is necessary

| slice            | value    |    n |   precision |   recall |   cost_per_trip |
|:-----------------|:---------|-----:|------------:|---------:|----------------:|
| pickup_hour      | 4        |  553 |      0.6070 |   0.9242 |          0.3580 |
| nonstandard_rate | 1        | 8424 |      0.0674 |   0.1534 |          0.3573 |
| pickup_hour      | 3        |  802 |      0.6173 |   0.9515 |          0.3529 |
| pickup_hour      | 6        | 1549 |      0.6139 |   0.9416 |          0.3525 |
| passenger_count  | nan      |  403 |      0.6667 |   0.9362 |          0.3474 |
| pickup_hour      | 5        |  637 |      0.6187 |   0.9311 |          0.3407 |
| pickup_borough   | Brooklyn |  699 |      0.4485 |   0.7625 |          0.3233 |
| pickup_hour      | 2        | 1216 |      0.6616 |   0.9572 |          0.3207 |

These overlapping slices are the highest-cost groups with n ≥ 200; the full slice report includes smaller groups. A useful aggregate ranking does not imply useful predictions in every group. Zones, fare and time describe trip context rather than intent, service quality, rider income or satisfaction. None of those missing concepts can be inferred as causal explanations.

There is only one held-out month. Seasonal shifts, future fares, recording changes and different payment interfaces can change performance. June was reused for feature/model/threshold choices, which makes development scores optimistic. Greedy feature selection is order dependent and uses logistic regression for all candidate groups. Rejected groups: **journey, calendar, passengers, rate, quality**.

No post-hoc calibration was fitted. The reliability diagram and Brier score are diagnostics; predicted probabilities should not be treated as guaranteed individual frequencies. The 500-resample paired bootstrap conditions on fixed predictions and treats trips as independent; it omits selection uncertainty and may understate uncertainty for correlated trips. No causal, fairness, economic-impact or full-year validation has been performed.

## Reproduction and governance

Run the README from a fresh clone. A local exclusive July lock prevents accidental repeat tuning; cached predictions support report recovery. This guard can be bypassed by manual file deletion, so research discipline and the recorded provenance remain necessary. Independent reruns of the same fixed method are replication, not fresh tests.

AI assistance is declared in the README. Team members must understand and verify the work. Peer review and classroom defense remain pending human activities. Future changes must be evaluated on a new, genuinely unseen period; do not optimize against this July result.
