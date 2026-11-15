"""Build the interactive dashboard: one self-contained HTML page with the anonymised data inlined.

    python deliverables/build_dashboard.py   ->  outputs/dashboard/index.html
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "outputs/dashboard_data.json").read_text())
html = (ROOT / "deliverables/dashboard_template.html").read_text()
blob = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")     # keep the JSON from closing its own script tag
out = ROOT / "outputs/dashboard"
out.mkdir(parents=True, exist_ok=True)
(out / "index.html").write_text(html.replace("__DATA__", blob))
print("wrote", out / "index.html", (out / "index.html").stat().st_size, "bytes")
