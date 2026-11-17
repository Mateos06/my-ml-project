# Original dataset

Unmodified source files from the instructor's [data-v2 release](https://github.com/evisp/ml-course-labs/releases/tag/data-v2):

| File | Contents |
| --- | --- |
| `yellow_tripdata_2026_sample.parquet` | Original 600,000-row yellow-taxi trip sample |
| `taxi_zone_lookup.csv` | Taxi-zone identifiers, boroughs and names |
| `taxi_zones.zip` | Original taxi-zone boundary archive |
| `data_dictionary_trip_records_yellow.pdf` | Yellow-taxi field definitions |

`manifest.json` records the source URL and SHA-256 checksum of each file. The trip sample and zone lookup match the fingerprints in `reports/selection.json`.

These files are included in Git. The analysis continues to read from the ignored `data/raw/` directory prepared by `python data/get_data.py`.
