"""Vendor licensed assets so the showcase needs no third-party runtime requests."""
from pathlib import Path
import hashlib
import io
import json
import tarfile
import requests

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"
headers = {"User-Agent":"TaxiTipLab/1.0 (educational project; licensed media attribution in site credits)"}
files = {}
for width in [960, 1280]:
    url=f"https://thumb.wikimedia.org/wikipedia/commons/thumb/d/d3/Yellow_Cabs_in_New_York.JPG/{width}px-Yellow_Cabs_in_New_York.JPG"
    response=requests.get(url, headers=headers, timeout=60)
    response.raise_for_status()
    target=ASSETS / "images" / f"nyc-taxis-{width}.jpg"
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(response.content)
    files[str(target.relative_to(ROOT))]={"source":url,"sha256":hashlib.sha256(response.content).hexdigest(),"bytes":len(response.content)}
metadata=requests.get("https://registry.npmjs.org/echarts/6.1.0",timeout=30).json()
response=requests.get(metadata["dist"]["tarball"],timeout=60)
response.raise_for_status()
with tarfile.open(fileobj=io.BytesIO(response.content),mode="r:gz") as archive:
    for source,name in [("package/dist/echarts.min.js","echarts.min.js"),("package/LICENSE","ECHARTS-LICENSE.txt"),("package/NOTICE","ECHARTS-NOTICE.txt")]:
        content=archive.extractfile(source).read()
        target=ASSETS / "vendor" / name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(content)
        files[str(target.relative_to(ROOT))]={"source":metadata["dist"]["tarball"]+"#"+source,"sha256":hashlib.sha256(content).hexdigest(),"bytes":len(content)}
(ASSETS / "asset-manifest.json").write_text(json.dumps(files,indent=2),encoding="utf-8")
print("Downloaded licensed Wikimedia thumbnails and Apache ECharts 6.1.0 with license/notice.")
