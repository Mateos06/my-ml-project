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

Walk from majority to May fare-band rule to depth-two tree to logistic regression/deeper single trees. Rejected feature additions: **journey, calendar, passengers, rate, quality**. Explain the 0.001 June AP gate, greedy order and shared representation. Selected model: **tree_depth_8**.

## 6. The result and its price · 8:30–11:00

July AP **0.747** with 95% interval **0.744–0.751**, versus baseline **0.585**. Precision **71.4%**, recall **95.0%**, top-20% lift **1.33×**. Explain AP versus accuracy and paired bootstrap differences. Threshold **0.32** follows FP=1, FN=2 assumed costs, not a default 0.5.

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
