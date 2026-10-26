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
             "Total weight", "Recent weight", "-330.0 lb", "-101.7 lb",
             "SYNTHETIC DEMONSTRATION"):
    assert term in text, f"Missing from PDF: {term}"
pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
pix.save(output / "inbody-synthetic-reference.png")
print(f"PASS: one-page PDF, {len(words)} words, no off-page text. Artifacts in {output}")
