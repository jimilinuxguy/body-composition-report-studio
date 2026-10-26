"""Render the real offline dataset and validate one-page PDF geometry."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import fitz
from app import Scan
from inbody_layout import build_inbody_pdf
entries = json.loads((ROOT / "data" / "measurements.json").read_text())["entries"]
scans = [Scan.model_validate(e) for e in entries]
assert len(scans) >= 6
pdf_bytes = build_inbody_pdf(scans[-1], scans)
output = ROOT / "test-results" / "pdf-qa"
output.mkdir(parents=True, exist_ok=True)
(output / "inbody-synthetic-reference.pdf").write_bytes(pdf_bytes)
doc = fitz.open(stream=pdf_bytes, filetype="pdf")
assert len(doc) == 1, f"Expected one page, got {len(doc)}"
page = doc[0]
words = page.get_text("words")
assert len(words) > 100
outside = [(w[4], w[:4]) for w in words if w[0] < 0 or w[1] < 0 or w[2] > page.rect.width or w[3] > page.rect.height]
assert not outside, f"Text outside page: {outside[:10]}"
text = page.get_text()
for term in ("Body Composition Analysis", "Muscle-Fat Analysis", "Obesity Analysis",
             "Segmental Lean Analysis", "Body Composition History", "Transformation Overview",
             "For personal tracking"):
    assert term in text, f"Missing from PDF: {term}"
# Verify each history label is inside the same visual band as its values.
# PyMuPDF coordinates increase down the page.
history_labels = ["Weight (lb)", "SMM (lb)", "PBF (%)", "ECW/TBW"]
history_area = page.search_for("Body Composition History")[0]
history_bounds = []
for label in history_labels:
    candidates = [r for r in page.search_for(label) if r.y0 > history_area.y1]
    assert candidates, f"History label not found: {label}"
    history_bounds.append(candidates[0])
for a, b in zip(history_bounds, history_bounds[1:]):
    assert 25 <= b.y0 - a.y0 <= 42, (
        f"History rows not uniformly aligned: {a} vs {b}"
    )
assert len(history_bounds) == 4
pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
pix.save(output / "inbody-synthetic-reference.png")
print(f"PASS: one-page PDF, {len(words)} words, no off-page text. Artifacts in {output}")
