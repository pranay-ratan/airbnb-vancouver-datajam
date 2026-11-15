"""Build the interactive pitch: one self-contained HTML page that presents like a deck but runs live.

The model and simulation JavaScript is lifted verbatim from the dashboard template, so the page,
the dashboard and src/ all compute the same way.

    python3 -I deliverables/build_pitch.py   ->  outputs/pitch/index.html
"""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
dash = (ROOT / "deliverables/dashboard_template.html").read_text()
START = "/* ---------------- model (mirrors src/assumptions.py) ---------------- */"
END = "/* ---------------- small chart builders ---------------- */"
model = dash[dash.index(START):dash.index(END)]
assert "function simulate(" in model and "function describe(" in model
data = json.loads((ROOT / "outputs/dashboard_data.json").read_text())
blob = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
html = (ROOT / "deliverables/pitch_template.html").read_text().replace("__MODEL__", model).replace("__DATA__", blob)
out = ROOT / "outputs/pitch"; out.mkdir(parents=True, exist_ok=True)
(out / "index.html").write_text(html)
print("wrote", out / "index.html", (out / "index.html").stat().st_size, "bytes")
