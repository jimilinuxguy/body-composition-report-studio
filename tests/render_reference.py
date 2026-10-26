"""Render the real offline dataset and validate one-page PDF geometry."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pymupdf as fitz
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
             "Research Parameters"):
    assert term in text, f"Missing from PDF: {term}"
# The full-history default must include the first and last dates/weights.
assert "May 2024" in text and "Oct 2026" in text, "Full history endpoints missing"
assert "522.4" in text and "192.4" in text, "Full history weights missing"
# Guard against explanatory captions intruding into the next section heading.
for heading in ("Obesity Analysis", "ECW / TBW Analysis"):
    heading_rect = page.search_for(heading)[0]
    nearby = [w for w in words if w[1] < heading_rect.y1 and w[3] > heading_rect.y0
              and w[0] < heading_rect.x1 and w[2] > heading_rect.x0]
    heading_words = set(heading.split())
    assert all(w[4] in heading_words for w in nearby), (
        f"Overlapping text at {heading}: {nearby}"
    )
# Full-width history replaces the two right-column sections.
assert "Results Interpretation" not in text
assert "Impedance (ohms)" not in text
for scan in scans:
    assert f"{scan.weight_lb:.1f}" in text

pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
pix.save(output / "inbody-synthetic-reference.png")
print(f"PASS: one-page PDF, {len(words)} words, no off-page text. Artifacts in {output}")
