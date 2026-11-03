# Every addition earns its place on June

The pipeline fits numeric median imputation, standard scaling and categorical one-hot encoding **on May only**. Unknown categories at prediction time are handled without refitting. An explicit allowlist drops all other columns, including tip, total charge and the target.

| Group      | Features                                | Reason available                             |
|:-----------|:----------------------------------------|:---------------------------------------------|
| fare       | Meter fare                              | Known at payment; numeric                    |
| journey    | Duration, distance, average speed       | Derived from completed trip                  |
| calendar   | Hour, cyclic hour, day of week          | Known pickup timestamp; no month feature     |
| geography  | Pickup/drop-off zones, borough, airport | Categorical zones; no false numeric ordering |
| passengers | Passenger count                         | Categorical; unknown retained                |
| rate       | Rate code                               | Known at end of trip                         |
| fees       | Seven pre-tip surcharges/fees           | Numeric; median imputation learned in May    |
| quality    | Unknown zone, rate and passenger flags  | Fixed deterministic rules                    |

Vendor ID, store-and-forward flag and request source are deliberately not candidates: this small study prioritizes interpretable trip information and avoids relying on provider or recording-system proxies. Tip percentage, tip amount, total amount, target and payment type are forbidden. Exclusion by design is distinct from losing an empirical feature comparison.

## The feature ledger

Starting with fare, test groups in the stated order with logistic regression; retain an addition only if June AP improves by at least 0.001. Later groups build on the retained set. This is an order-dependent, greedy comparison, not an exhaustive test of all interactions or separate leave-one-feature-out effects. Tree models share this selected representation; a tree-specific selection could produce a different result.

| addition   | groups_tested                  |   june_ap |   delta_ap | retained   | reason                       |
|:-----------|:-------------------------------|----------:|-----------:|:-----------|:-----------------------------|
| fare       | fare                           |    0.7479 |     0.0000 | True       | predeclared starting feature |
| journey    | fare, journey                  |    0.7460 |    -0.0019 | False      | gain below 0.001 AP          |
| calendar   | fare, calendar                 |    0.7471 |    -0.0008 | False      | gain below 0.001 AP          |
| geography  | fare, geography                |    0.7532 |     0.0053 | True       | gain >= 0.001 AP             |
| passengers | fare, geography, passengers    |    0.7531 |    -0.0002 | False      | gain below 0.001 AP          |
| rate       | fare, geography, rate          |    0.7528 |    -0.0004 | False      | gain below 0.001 AP          |
| fees       | fare, geography, fees          |    0.7617 |     0.0085 | True       | gain >= 0.001 AP             |
| quality    | fare, geography, fees, quality |    0.7620 |     0.0003 | False      | gain below 0.001 AP          |

**Rejected additions:** journey, calendar, passengers, rate, quality. Rejection means the feature group did not meet this procedure's June improvement rule; it does not establish that it has no information.

## The baseline ladder and model comparison

The May-derived rule selects fare band **0–10**. A majority decision uses a 0.5 threshold on constant May prevalence; a majority baseline can therefore have zero recall. The depth-two tree is the final rung of the simple baseline ladder. Each learned model has its own cost-minimizing June threshold.

| model                  |      n |   average_precision |   precision |   recall |   lift_at_20pct |   cost_per_trip |   threshold |
|:-----------------------|-------:|--------------------:|------------:|---------:|----------------:|----------------:|------------:|
| majority               | 123162 |              0.5954 |      0.5954 |   1.0000 |          1.0000 |          0.4046 |      0.5000 |
| fare_rule              | 123162 |              0.6647 |      0.7652 |   0.4082 |          1.2852 |          0.7793 |      0.7614 |
| logistic               | 123162 |              0.7617 |      0.7003 |   0.9404 |          1.3277 |          0.3106 |      0.4200 |
| tree_depth_2           | 123162 |              0.7157 |      0.6579 |   0.9715 |          1.2261 |          0.3347 |      0.3900 |
| tree_depth_4           | 123162 |              0.7485 |      0.7197 |   0.9257 |          1.3298 |          0.3031 |      0.4700 |
| tree_depth_6           | 123162 |              0.7585 |      0.7199 |   0.9446 |          1.3363 |          0.2848 |      0.3200 |
| tree_depth_8           | 123162 |              0.7637 |      0.7251 |   0.9454 |          1.3383 |          0.2784 |      0.3200 |
| tree_depth_6_leaf_1000 | 123162 |              0.7630 |      0.7104 |   0.9480 |          1.3355 |          0.2920 |      0.3100 |

**Selected: tree_depth_8**, using fare, geography, fees. Ranking uses June AP; the operating threshold is a separate cost decision. June AP is a development score after multiple choices, not an unbiased estimate of future performance.

[Download the feature ledger](downloads/feature_comparison.csv) · [Download the complete June table](downloads/validation_metrics.csv)

## Read the two-level tree

```text
Numeric split thresholds are in May-standardized units. One-hot splits use 0/1.

|--- numeric__fare_amount <= -0.10
|   |--- numeric__congestion_surcharge <= -1.34
|   |   |--- class: 0
|   |--- numeric__congestion_surcharge >  -1.34
|   |   |--- class: 1
|--- numeric__fare_amount >  -0.10
|   |--- numeric__extra <= -0.54
|   |   |--- class: 0
|   |--- numeric__extra >  -0.54
|   |   |--- class: 0

```

The numeric thresholds shown here are standardized by the May-fitted scaler. They are not raw dollar amounts. The root and its immediate child splits are the two decision levels.

## Leakage tests

Tests perturb every forbidden column and verify predictions remain identical, pass unseen zones and extreme validation values without changing fitted imputer statistics, check exact temporal boundaries, and exercise both the post-July development refusal and cached-result path. Numeric thresholds in cleaning are constants, not quantiles estimated from the combined months.
