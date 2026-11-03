"""Verify generated local links/assets and the threshold explorer's input."""
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "dist"


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in {"href", "src", "data-source"} and value:
                self.links.append(value)


broken, checked = [], 0
for page in SITE.rglob("*.html"):
    parser = Links()
    parser.feed(page.read_text(encoding="utf-8"))
    for link in parser.links:
        url = urlsplit(link)
        if url.scheme or url.netloc or not url.path:
            continue
        target = (SITE / unquote(url.path).lstrip("/") if url.path.startswith("/")
                  else page.parent / unquote(url.path)).resolve()
        if target.is_dir():
            target = target / "index.html"
        checked += 1
        if not target.is_file():
            broken.append((str(page.relative_to(SITE)), link))
rows = json.loads((SITE / "assets" / "thresholds.json").read_text())
assert len(rows) == 101 and all({"threshold", "cost_per_trip", "fp", "fn"} <= set(row) for row in rows)
if broken:
    raise SystemExit(f"Broken links: {broken}")
print(f"Checked {checked} local links/assets and 101 threshold entries; no broken targets.")
