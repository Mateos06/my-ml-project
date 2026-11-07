# Behind the visual lab

The homepage is the short, interactive story. The original [problem card](problem.md), [cleaning report](data.md), [feature ledger](features.md), [evaluation](evaluation.md), [model card](model-card.md), and [notebooks](reproduce.md#download-the-four-notebooks) retain the full academic evidence.

## What each exhibit uses

| Exhibit | Evidence | Important limit |
| --- | --- | --- |
| Tip, fare, hour, weekday, airport and journey charts | Cleaned May card trips and saved rate tables | Associations, not causal effects |
| Cleaning funnel | Ordered audit for the selected month | Counts follow actual pickup timestamps |
| Taxi-zone map | Supplied TLC shapefile and May pickup-zone aggregates | Rates with fewer than 200 trips are not colored |
| Feature comparison | Saved June feature-group ledger | Greedy, order-dependent selection |
| Model dashboard | Saved June and July metric tables | Logistic regression was compared on June, not scored in the final July pass |
| Precision–recall and reliability curves | Cached predictions and saved calibration bins | No refitting or new July scoring |
| Error examples | Two existing July prediction errors, shown with binned journey context | Illustrative individual errors, not representative estimates |
| Trip predictor | Exported frozen model and preprocessing | An uncertain estimate for eligible card trips |

The fare-and-tip calculator and cash-tip slider explain measurement. Their adjustable amounts are illustrations, not observed trips or model predictions.

## The result to remember

The selected depth-eight tree achieved **0.747 average precision** on July, versus **0.585** for the constant-score baseline. Its trip-bootstrap 95% interval is **0.744–0.751**. At the June-selected **0.32** threshold, precision is **71.4%** and recall is **95.0%**.

These estimates apply to **119,811 eligible July card trips**. They do not measure cash tipping, individual character, or a full year of performance. The [complete evaluation](evaluation.md) explains costs, paired intervals, calibration and failure slices.

## How browser inference works

`scripts/export_lab.py` exports the actual May-fitted numeric medians, scaling parameters, one-hot category vocabulary, split thresholds and leaf probabilities. `model-runtime.js` applies them in the same order as the Python pipeline, including float32 conversion before tree comparisons.

The selected model uses **fare, geography and pre-tip fees**. Duration, distance, hour, weekday and passenger count are available as trip context; their rejected feature groups do not change this frozen tree's probability. Tip amount and total charge are excluded.

`scripts/check_browser_model.cjs` compared the JavaScript interpreter with scikit-learn on **1,000 May trips**: maximum probability difference **0**, with identical class decisions. It also checks that forbidden and unused fields cannot change the score. This is an implementation check, not additional model validation.

Predictions run locally in the browser. The form sends no trip details to a server. The displayed path explains which splits were followed; it is not a causal explanation or a feature-attribution study.

## Geographic precision

The map uses the supplied shapefile's **NAD83 / New York Long Island StatePlane coordinates, in US survey feet**. A uniform affine transform fits those real boundaries to the SVG canvas, preserving aspect ratio. Display coordinates are rounded to one tenth of a screen unit; no latitude or longitude is invented.

Pickup counts and rates come from eligible May trips. Gray zones lack the 200-trip minimum for rate coloring. Unknown zones have no boundary. Airport labels use zone **1 = Newark (EWR)**, **132 = JFK**, and **138 = LaGuardia (LGA)**.

## Rebuild the presentation

The committed browser exports and licensed assets are sufficient for an ordinary static MkDocs build. Training and raw downloads are not required just to preview the website.

```bash
python -m mkdocs build --strict
python -m mkdocs serve
```

After reproducing the full study using the README, refresh the interactive data and check browser inference:

```bash
python scripts/export_lab.py
node scripts/check_browser_model.cjs
python -m mkdocs build --strict
python scripts/check_site.py
```

The exporter reads May for descriptive aggregates, reads saved June/July prediction caches, and checks frozen provenance. It does not fit models or call July prediction again. Node.js is needed for the cross-language check; it is not needed by the hosted static site.

`overrides/lab.html` contains the visual presentation. A MkDocs hook assigns it to the homepage, so regenerating the academic reports does not replace the redesign. The full reports remain available through the documentation navigation.

## Photography

**“Yellow Cabs in New York.JPG” — ChevronZ, 6 August 2010.** [Original file and author attribution on Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Yellow_Cabs_in_New_York.JPG). Licensed under [Creative Commons Attribution–ShareAlike 3.0](https://creativecommons.org/licenses/by-sa/3.0/).

The site serves Wikimedia's 960- and 1280-pixel thumbnails locally. The downloaded files were not retouched. The hero displays them with a responsive crop and a CSS dark overlay; this presentation adaptation is offered under the same CC BY-SA 3.0 license. The photo is contextual imagery from 2010, not an image of the 2026 sample trips. No photographer endorsement is implied.

## Chart library and provenance

Charts use **Apache ECharts 6.1.0**, vendored locally from its npm package. See the bundled [license](assets/vendor/ECHARTS-LICENSE.txt), [notice](assets/vendor/ECHARTS-NOTICE.txt), and [Apache ECharts project](https://echarts.apache.org/).

The [asset manifest](assets/asset-manifest.json) records original download URLs, file sizes and SHA-256 hashes. `scripts/fetch_lab_assets.py` can restore the photograph thumbnails and pinned chart-library assets. The [study sources](sources.md) identify the instructor sample, TLC definitions and metric references.

The redesign preserves the recorded model selection and final evaluation. Animation, chart selections and threshold exploration are presentation controls; they do not change the trained model, the frozen July threshold or the submitted results.
