"""Download the instructor's fixed sample. Run: python data/get_data.py."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

BASE = "https://github.com/evisp/ml-course-labs/releases/download/data-v2/"
FILES = [
    "yellow_tripdata_2026_sample.parquet", "taxi_zone_lookup.csv",
    "taxi_zones.zip", "data_dictionary_trip_records_yellow.pdf",
]
RAW = Path(__file__).resolve().parent / "raw"


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        target = RAW / name
        if not target.exists():
            print(f"Downloading {name}", flush=True)
            temporary = target.with_suffix(target.suffix + ".part")
            try:
                urllib.request.urlretrieve(BASE + name, temporary)
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
    with zipfile.ZipFile(RAW / "taxi_zones.zip") as archive:
        for member in archive.infolist():
            target = (RAW / member.filename).resolve()
            if not target.is_relative_to(RAW.resolve()):
                raise ValueError(f"Unsafe archive member: {member.filename}")
        archive.extractall(RAW)
    manifest = {
        "source": BASE,
        "files": {name: hashlib.sha256((RAW / name).read_bytes()).hexdigest() for name in FILES},
    }
    (RAW / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Ready:", RAW)


if __name__ == "__main__":
    main()
