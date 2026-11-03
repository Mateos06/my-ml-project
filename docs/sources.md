# Sources and metric definitions

- [Instructor fixed-sample release, data-v2](https://github.com/evisp/ml-course-labs/releases/tag/data-v2). The downloader uses exactly this release; SHA-256 hashes identify the files used.
- [NYC TLC trip-record data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page). Dataset context and official download reference. TLC cautions that provider-supplied trip records can contain inaccuracies.
- [Official yellow-taxi data dictionary](https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf). Field and code meanings, including the scope of recorded tips. The instructor's copy is also downloaded locally.
- [Scikit-learn average precision](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html). The primary metric is non-interpolated AP, not trapezoidal PR area.
- [Scikit-learn pitfalls and data leakage](https://scikit-learn.org/stable/common_pitfalls.html). Pipelines keep fitted preprocessing in the training process.
- [MkDocs deployment guide](https://www.mkdocs.org/user-guide/deploying-your-docs/). The website builds to static assets; GitHub Pages can host them.

The supplied project brief defines the academic task and target. Our fixed cleaning cutoffs, practical-effect marker, candidate model grid and cost assumptions are project decisions, not official TLC rules. All reported metric values come from this repository's saved computations rather than external publications.
