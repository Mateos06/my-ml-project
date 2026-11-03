# Will this passenger tip well?

Predict whether an eligible NYC yellow-taxi **card trip** ends with a recorded tip of at least **25% of the meter fare**, using information available at the payment screen before the tip is entered.

## Population and target

`generous_tip = 1[tip_amount >= 0.25 * fare_amount]`. Exactly 25% counts. The denominator is the meter fare, not the pre-tip total, distance, or total charge. We require a finite, positive fare and a finite, nonnegative tip.

Cash tips are unobserved: cash zeros cannot establish that passengers did not tip. Restrict to `payment_type == 1`. This also excludes flex fares (0), no-charge (3), disputes (4), unknown (5), and voided trips (6). We cannot generalize the result to those populations. Flex fares are explicitly excluded by the card-tip question, not because their missing passenger counts are imputed away.

Keep nonstandard rates, unknown zones, and missing passengers with explicit flags. Drop exact duplicate rows, negative or infinite fees, durations outside 0.5–240 minutes, distances outside 0.01–100 miles, and mean speeds above 100 mph. These are fixed plausibility policies, not learned outlier quantiles. Missing fees are retained and imputed inside a May-fitted pipeline. Very large valid tips stay in the target; the histogram alone pools values over 100% in its last bin.

## Moment of prediction

The trip has ended. Fare, journey time, measured distance, end-of-trip rate code, pickup/drop-off zones, time, passengers, and pre-tip fees are available. `tip_amount`, `tip_pct`, the target, and `total_amount` are forbidden predictors. Payment type determines the study population; it is not a model feature. No driver, customer or vendor identity is used.

## Split and selection contract

- May 2026 pickups: fit every imputer, encoder, scaler and model; inspect descriptive patterns and define the fare rule.
- June 2026 pickups: judge each feature group, select model depth and threshold, inspect calibration and slices. June estimates are optimistic after multiple choices.
- July 2026 pickups: one scoring pass after code, data, features, model and threshold are frozen. Cache predictions and bootstrap them without refitting or rescoring.

Split by pickup time, even if a trip ends in the next month. Do not randomly shuffle the months or refit on June. A completed run is locked; a fresh clone can independently reproduce it, but repeating the study never creates a new independent test set.

## Baseline ladder and success

1. Majority-class decision fitted from May; constant May prevalence for probability metrics.
2. A fare-band rule: predict positive only for the May band with the largest positive rate and at least 200 observations; score with two May rates.
3. A single decision tree of maximum depth two.
4. Logistic regression and single trees of depths 4, 6 or 8; no boosting or ensembles.

Primary ranking metric: average precision (AP), explicitly the non-interpolated PR AUC used by scikit-learn. Also report precision, recall, lift in the top 20%, Brier score, confusion counts, cost and slice counts. Ties at the top-20% boundary are fractionally weighted.

For a hypothetical optional driver insight, assume a false positive costs **1 unit** (an unhelpful prompt) and a false negative costs **2 units** (a missed useful insight). These are illustrative relative costs, not measured dollars. Choose the June threshold minimizing `(FP + 2 FN) / n` over a fixed 0.01 grid plus an all-negative option; ties favor the higher threshold. There is no claim of deployment value without validating those costs.

Retain a feature group only if it improves June AP by at least 0.001 in a fixed greedy order. Report rejected groups. Choose the final model by June AP, with cost and then name as deterministic tiebreakers. A five-percentage-point difference from the May overall rate is our descriptive practical-effect marker; it is not a hypothesis test.

The outcome is evidence about the predictive limits of these features and models. A small uplift or a failure to beat a baseline is a valid finding. This experiment does not identify the irreducible ceiling of human generosity.
