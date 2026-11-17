# The Tipping Point

**Predicting Recorded Generous Card Tips in New York City Yellow Taxis: A Reproducible Temporal Classification Study**

**Team D · Machine Learning Project**  
Research paper · 17 November 2026  
Study period: May–July 2026 · Recorded evaluation: 3 November 2026

## Abstract

This study examines whether information available at the end of a taxi trip can predict a recorded card tip of at least 25% of the meter fare. An instructor-provided sample contains 600,000 New York City yellow-taxi records. After restricting the population to eligible card payments and applying fixed data-quality rules, 372,929 trips remain across May, June, and July 2026. May supplies 129,956 training observations, June supplies 123,162 validation observations, and July supplies 119,811 held-out test observations. All learned preprocessing and model fitting use May only. Feature groups, model complexity, and decision thresholds are selected using June; July predictions are generated once after the analysis is frozen. Comparisons include a constant-score majority baseline, a fare-band rule, logistic regression, and individual decision trees. The selected depth-eight tree uses fare, geography, and pre-tip fees. On July, its average precision is 0.7474, compared with 0.5845 for the constant-score baseline; the paired bootstrap interval for the improvement is 0.1601–0.1657. At the June-selected threshold of 0.32, precision is 71.37%, recall is 94.97%, and hypothetical cost is 0.2815 units per trip, versus 0.4155 for the majority decision. Performance is uneven across trip types, particularly nonstandard fares. The findings establish predictive signal within the observed card-payment population, while leaving causal explanations, unrecorded cash tips, future-season generalization, and operational benefits unresolved.

**Keywords:** taxi trip records; binary classification; recorded tipping; temporal validation; average precision; decision trees; reproducibility.

## 1. Introduction

Taxi trip records connect an observed payment outcome with measurable features of a completed journey. They therefore offer a practical setting for studying a central machine-learning question: how much can a model predict from information that is actually available when a decision must be made? For this project, the decision moment is the payment screen after a trip ends and before the passenger enters a tip. Fare, completed-trip distance and duration, location identifiers, and pre-tip fees are available at that point.

The project asks whether these features help predict a recorded tip meeting a specified threshold. It deliberately defines “generous” as a label in the dataset: a tip of at least 25% of a positive meter fare. The term does not measure a passenger's character, intent, satisfaction, or total generosity. Cash tips are not observed in the same way as card tips, and the dataset does not contain the social and service context needed to explain why a person tips.

The practical motivation is an educational, hypothetical driver-support insight. A positive prediction could indicate that a completed trip resembles previously observed trips meeting the recorded-tip threshold. The study does not establish that such information would improve service or income. Because the journey has already ended at prediction time, these results also do not validate a system for deciding which trips to accept or where to drive beforehand.

Three research questions organize the analysis. **RQ1:** Can permitted pre-tip features outperform simple baselines on a later month? **RQ2:** Which candidate feature groups improve validation performance under a fixed selection procedure? **RQ3:** What do decision costs, uncertainty, calibration diagnostics, and subgroup errors reveal beyond a single aggregate score?

The contribution is a transparent empirical workflow rather than a new learning algorithm. It connects an observable target, an auditable population definition, chronological separation of training and evaluation, explicit feature selection, and a frozen final comparison. The accompanying notebooks, source package, original dataset, reports, and interactive website make these decisions inspectable. All empirical results in this paper come from the repository's saved analysis; writing the paper did not initiate another model fit or July scoring pass.

## 2. Background and methodological context

The NYC Taxi and Limousine Commission publishes trip records containing timestamps, locations, distances, fares, payment types, and passenger counts. The records originate from reporting technology providers, and TLC does not guarantee their accuracy. They require substantive validation before modeling. [1](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)

The yellow-taxi data dictionary is particularly important for interpreting the outcome: recorded tips reflect card transactions, while cash tips are absent from that field. A zero cash-tip entry therefore cannot be treated as evidence that no tip was paid. This measurement distinction motivates the card-only study population. [2](https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf)

The methodological basis combines straightforward supervised learning with controls against information leakage. Fitting preprocessing on training data and applying the same transformations to later observations prevents validation and test information from entering learned statistics. Pipelines support this separation. [3](https://scikit-learn.org/1.8/common_pitfalls.html) Individual decision trees provide nonlinear partitions and readable rules; depth and minimum leaf size constrain their complexity. [4](https://scikit-learn.org/1.8/modules/tree.html)

Ranking quality, probability quality, and a thresholded decision answer different questions. Average precision summarizes a precision–recall curve using recall increments rather than trapezoidal interpolation. [5](https://scikit-learn.org/1.8/modules/generated/sklearn.metrics.average_precision_score.html) Reliability diagrams compare predicted probabilities with observed event frequencies, while the Brier score measures overall probabilistic error and is not a pure measure of calibration. [6](https://scikit-learn.org/1.8/modules/calibration.html) Bootstrap resampling provides a framework for estimating sampling variability, subject to the assumptions of the resampling unit and procedure. [7](https://doi.org/10.1214/aos/1176344552)

This is a focused empirical application of those methods. It does not claim an exhaustive review of tipping research or compare against published taxi models evaluated on incompatible samples. Its comparisons use the same project population and temporal protocol.

## 3. Dataset, target, and study population

### 3.1. Source and temporal coverage

The exact input is the instructor's fixed `data-v2` release, rather than a newly collected extract of the full TLC archive. [8](https://github.com/evisp/ml-course-labs/releases/tag/data-v2) It contains a 600,000-row, 21-column Parquet sample and supporting zone and field-definition assets. The repository now includes the four unmodified source files in `data/dataset/`, together with SHA-256 checksums. The sampling mechanism and any instructor preparation are not independently reconstructed here; population-wide representativeness cannot be assumed from the sample size alone.

An audit of recorded pickup timestamps identifies two April rows, 199,999 May rows, 200,001 June rows, and 199,998 July rows. The two April records fall outside the specified analysis windows. Assignment uses pickup time even when a trip ends in the next month. This distinction avoids assuming exactly 200,000 records in each calendar split.

**Table 1. Temporal cohorts and observed class balance.**

| Pickup month | Role | Raw rows | Eligible rows | Positive labels | Positive rate |
| --- | --- | ---: | ---: | ---: | ---: |
| May 2026 | Training | 199,999 | 129,956 | 72,992 | 56.17% |
| June 2026 | Validation and selection | 200,001 | 123,162 | 73,329 | 59.54% |
| July 2026 | Final test | 199,998 | 119,811 | 70,035 | 58.45% |
| Total in the three splits | Study population | 599,998 | 372,929 | 216,356 | — |

Source: `reports/tables/pickup_month_audit.csv`, the three cleaning audits, `reports/selection.json`, and the June/July metric tables. Positive rates use eligible rows, not all raw records.

![Temporal study design: May fits the model, June selects it, and July evaluates the frozen choice.](figures/study-design.png)

*Figure 1. Chronological separation of responsibilities. The diagram summarizes saved cohort counts; it does not represent a new analysis run.*

### 3.2. Target and information available at prediction

For an eligible card-paid trip, the binary outcome is defined by:

**y = 1{tip_amount ≥ 0.25 × fare_amount}.**

Exactly 25% is positive. The denominator is the meter fare, not the total charge or a pre-tip sum of fare and surcharges. For example, a $5 recorded card tip on a $20 fare is positive, while a $4 tip on that fare is negative. The study requires a finite, strictly positive fare and a finite, nonnegative tip to construct this outcome.

Permitted predictors describe the completed trip before tip entry. The feature allowlist excludes `tip_amount`, `tip_pct`, `generous_tip`, and `total_amount`; total charge is especially problematic because it already contains the outcome. `payment_type` identifies the eligible population but is also excluded from predictors. Driver, rider, and vendor identifiers are not used. Vendor, store-and-forward, and request-source variables are excluded by design rather than rejected by an empirical feature comparison.

Eligibility uses the recorded tip to establish whether a valid retrospective label exists. An operational system would need a separate policy for missing or invalid future outcomes; the retrospective filter is not a claim that the tip is known before prediction.

### 3.3. Payment observability

The May payment audit demonstrates why payment type cannot be ignored. Of 199,999 raw May trips, 133,571 are coded as card payments, 18,149 as cash, and 46,601 as flex fares. The remaining 1,678 have no-charge or disputed codes. Among the 17,934 cash trips meeting the audit's fare/tip validity condition, the recorded nonzero-tip rate is zero. That is a property of the recording process, not a measured absence of cash tipping.

For the corresponding 133,558 valid card trips before journey-quality filtering, 90.19% have a nonzero recorded tip and 56.10% meet the 25% threshold. Restricting to `payment_type == 1` therefore aligns the target with its observation mechanism. Flex fares and other payment codes remain outside scope even when a tip entry exists. The final May prevalence changes slightly to 56.17% after all cleaning steps.

### 3.4. Cleaning and retained uncertainty

Cleaning is deterministic and applied separately after the temporal read. It first removes exact duplicates, keeps card payments, validates the fare and tip, and rejects negative or infinite component charges. It then retains durations from 0.5 to 240 minutes, distances from 0.01 to 100 miles, and average speeds no greater than 100 mph. These cutoffs are fixed project policies, not quantiles fitted on combined data. Their plausibility does not imply that every excluded trip is erroneous.

**Table 2. Remaining observations after each ordered cleaning decision.**

| Step | May | June | July |
| --- | ---: | ---: | ---: |
| Raw rows within the month | 199,999 | 200,001 | 199,998 |
| Remove exact duplicates | 199,999 | 200,001 | 199,998 |
| Keep observable card payments | 133,571 | 126,923 | 123,446 |
| Require positive finite fare | 133,558 | 126,898 | 123,387 |
| Require valid nonnegative tip | 133,558 | 126,898 | 123,387 |
| Require nonnegative finite charges | 133,558 | 126,898 | 123,387 |
| Apply duration bounds | 130,303 | 123,541 | 120,213 |
| Apply distance bounds | 129,961 | 123,162 | 119,826 |
| Apply average-speed bound | 129,956 | 123,162 | 119,811 |

Source: `reports/tables/cleaning_train.csv`, `cleaning_validation.csv`, and `cleaning_test.csv`. Missing component fees are retained for training-fitted imputation; “finite charges” means infinite values are rejected, not that missing fees are discarded. The unchanged rows show that a rule may be implemented without removing additional observations in this sample.

Uncertain metadata is handled explicitly instead of deleting every affected row. Zone identifiers outside the integer range 1–263 are mapped to category 265 and flagged. Missing or invalid passenger counts become an unknown category. Nonstandard rate codes remain in the data with an indicator. The May cohort contains 759 trips with an unknown zone, 12,034 with a nonstandard rate, and 516 with unknown passenger count; these flags can overlap. Valid large tips remain in the target, while the descriptive histogram alone pools tip percentages above 100% into its final bin.

The raw May audit also records 46,601 missing passenger counts and rate codes, alongside a completely missing `request_source` field. These counts describe the raw population and should not be confused with the much smaller unknown-passenger count after eligibility and cleaning. Negative fees and fares are dropped according to the ordered rules rather than converted to positive amounts. `total_amount` is audited but does not determine eligibility or model inputs.

## 4. Methods

### 4.1. Temporal development and final evaluation

Every imputer, scaler, encoder, and estimator is fitted using May observations only. June supplies feature-group comparisons, model selection, cost-based thresholds, and development diagnostics. The selected model is not refitted on combined May and June data. July evaluates that unchanged fitted model and the frozen thresholds.

The implementation stores hashes of the source, data, zone lookup, and serialized models. Before final scoring, it verifies those fingerprints and creates an exclusive `artifacts/july.lock`. Predictions are saved before subsequent reporting and bootstrap calculations. A completed final run returns its saved result; development refuses to proceed after the lock exists. These controls reduce accidental reuse, although manual deletion could bypass them. Research discipline is therefore still necessary.

### 4.2. Feature construction and preprocessing

Eight groups represent hypotheses about potentially useful trip context. Duration comes from the difference between recorded drop-off and pickup times; average speed combines duration and distance. Calendar fields include pickup hour, cyclic sine/cosine encodings, and day of week. Airport status indicates whether pickup or drop-off uses the EWR, JFK, or LGA zone identifiers. Zone identifiers are categorical, preventing their numbers from being treated as an ordered geographical scale.

**Table 3. Candidate feature groups and their representations.**

| Group | Candidate information | Representation |
| --- | --- | --- |
| Fare | Meter fare | Numeric |
| Journey | Duration, trip distance, average speed | Numeric |
| Calendar | Pickup hour, sine/cosine of hour, day of week | Numeric and categorical |
| Geography | Pickup/drop-off zones, pickup borough, airport indicator | Categorical zones/borough; numeric indicator |
| Passengers | Passenger count, including unknown | Categorical |
| Rate | End-of-trip rate code | Categorical |
| Fees | Extra, MTA tax, tolls, improvement surcharge, congestion surcharge, airport fee, CBD congestion fee | Numeric |
| Quality | Unknown-zone, nonstandard-rate, unknown-passenger flags | Numeric indicators |

Numeric preprocessing uses median imputation with empty features retained, followed by standard scaling. Categorical values are converted to strings, missing entries become `Unknown`, and one-hot encoding ignores unseen categories at prediction time. A column transformer drops all columns outside the chosen groups. These transformations are learned in the same May-fitted pipeline as each estimator.

### 4.3. Feature selection

Selection starts with fare and tests the remaining groups in the fixed order shown in Table 3. Each proposed addition is evaluated with logistic regression. It is retained only when June average precision increases by at least 0.001 relative to the current retained set. Later proposals build on accepted groups, and rejected proposals are recorded as well as successful ones.

This is a greedy, order-dependent procedure. It is not an exhaustive search, a statistical test of a feature's intrinsic value, or a leave-one-group-out analysis. Because logistic regression drives selection, the resulting representation may not be optimal for decision trees. The selected representation is subsequently shared by all learned model candidates.

### 4.4. Baselines and model candidates

The first baseline returns the May positive prevalence, 0.561667, for every observation. At a 0.5 threshold it predicts the positive majority class for all June and July trips. Its average precision equals the evaluated month's positive prevalence, although its constant probability is learned from May. Its top-20% lift is one.

The second baseline is a deliberately simple fare-band rule. May selects the fare band with the highest positive rate among bands containing at least 200 observations. The selected band is (0, 10] dollars, with positive rate 0.761414. Trips in that band receive that score; all other bands receive the lowest May band rate, 0.163620. Thresholding at the high score therefore flags only the selected band. The lower score is not an estimated pooled probability for the complement, which helps explain this rule's weak Brier score. The rule is primarily an interpretable decision baseline.

Learned candidates comprise logistic regression and single decision trees with maximum depths 2, 4, 6, and 8 and a minimum leaf size of 200. An additional depth-six tree uses a minimum leaf size of 1,000. Logistic regression uses `C=1.0`, `solver=lbfgs`, and `max_iter=1500`. The recorded implementation uses scikit-learn 1.8.0, with its default L2 logistic regularization and default Gini tree criterion. The seed is 2026. No boosting, random forest, or other ensemble is fitted.

June average precision selects the final learned model, with cost and then model name providing deterministic tie-breaking. Each learned candidate has its own June-selected cost threshold. The depth-two tree also serves as the strongest member of the simple baseline ladder. Its exported numeric split values are in May-standardized units and must not be read as dollar values. Its printed class labels reflect the tree's default class choice, whereas evaluation uses a separate threshold on predicted probabilities.

### 4.5. Metrics and the decision threshold

Average precision (AP) is the primary ranking measure. It weights the precision at each score cutoff by the associated increment in recall. The project uses scikit-learn's non-interpolated definition rather than trapezoidal precision–recall area. AP is not classification accuracy. Positive labels account for roughly 56–60% of eligible trips, so this is not a rare-event classification problem; AP is chosen to emphasize the quality of positive predictions across cutoffs.

At a fixed threshold, precision is `TP / (TP + FP)` and recall is `TP / (TP + FN)`. Top-20% lift divides the positive proportion among the highest-scoring fifth of trips by overall prevalence. The implementation uses the ceiling of 20% of the sample size and fractionally includes score ties at the boundary, preventing tied tree scores or constant baseline scores from benefiting from row order. The Brier score is the mean squared difference between probability and binary outcome.

The illustrative decision exercise assigns one unit to a false positive and two to a false negative:

**Cost per trip = (FP + 2 × FN) / n.**

These units express a hypothetical relative preference, not observed financial loss. June threshold selection searches 0.00 through 1.00 in steps of 0.01 and an additional all-negative option at 1.000001. Equal-cost choices favor the higher threshold. The selected model's threshold is 0.32. Model ranking and threshold selection remain distinct: a model can rank well while making costly decisions at a particular cutoff.

### 4.6. Uncertainty and subgroup analysis

The final analysis uses 500 paired trip-level bootstrap samples, with replacement and seed 2026. Within each resample, identical indices evaluate the selected model and the majority baseline. The 2.5th and 97.5th percentiles provide intervals for each metric and its model-minus-baseline difference. Predictions remain fixed: the bootstrap does not refit the model or repeat feature and threshold selection.

These intervals describe conditional sampling variation under independent-trip resampling. Shared drivers, operating conditions, or time clusters could make trips dependent, while the repeated use of June introduces selection uncertainty that is not represented. Consequently, the intervals are not guarantees about new months or new modeling procedures.

Descriptive May rate tables use Wilson 95% intervals. A difference of at least five percentage points from May's overall rate is marked as practically large by project policy, without multiple-testing correction or a causal interpretation. Final subgroup reports cover fare, distance, duration, pickup hour, day of week, airport status, passengers, borough, unknown zones, and nonstandard rates. Groups below 200 observations are flagged as small. Slices overlap and their sample sizes cannot be added together.
