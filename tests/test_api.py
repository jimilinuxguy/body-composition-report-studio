from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

VALID_SCAN = {
    "report_type": "inbody",
    "name": "Test Client",
    "scan_date": "2026-10-25",
    "source": "estimated",
    "height_in": 71,
    "weight_lb": 170,
    "body_fat_pct": 15,
    "notes": "",
    "field_sources": {"right_arm_fat_lb": "measured"},
    "right_arm_fat_lb": 4.2,
}


def test_home_returns_html():
    response = client.get("/")
    assert response.status_code == 200
    assert 'id="segmental-preview"' in response.text
    assert '/static/app.js' in response.text


def test_static_javascript_served():
    response = client.get("/static/app.js")
    assert response.status_code == 200
    assert "function update()" in response.text


def test_pdf_accepts_blank_notes_and_regional_data():
    response = client.post("/api/pdf", json=VALID_SCAN)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content.startswith(b"%PDF")
    assert len(response.content) > 1000


def test_report_preserves_regional_data_and_provenance():
    response = client.post("/api/report", json=VALID_SCAN)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["scan"]["right_arm_fat_lb"] == 4.2
    assert data["scan"]["field_sources"]["right_arm_fat_lb"] == "measured"
    assert data["metrics"]["fat_mass_lb"] == 25.5


def test_invalid_measurement_is_rejected():
    payload = {**VALID_SCAN, "body_fat_pct": 110}
    response = client.post("/api/pdf", json=payload)
    assert response.status_code == 422


def test_dexa_pdf():
    payload = {**VALID_SCAN, "report_type": "dexa", "arms_fat_pct": 12.3}
    response = client.post("/api/pdf", json=payload)
    assert response.status_code == 200, response.text
    assert response.content.startswith(b"%PDF")

def test_reference_layout_pdf_has_all_required_sections():
    import io
    from pypdf import PdfReader
    response = client.post("/api/inbody/sheet", json={"scan": VALID_SCAN, "history": []})
    assert response.status_code == 200, response.text
    reader = PdfReader(io.BytesIO(response.content))
    assert len(reader.pages) == 1
    page = reader.pages[0]
    assert abs(float(page.mediabox.height) - 841.89) < 2
    text = page.extract_text()
    for heading in (
        "Body Composition Analysis", "Muscle-Fat Analysis", "Obesity Analysis",
        "Segmental Lean Analysis", "ECW / TBW Analysis", "Body Composition History",
        "Segmental Fat Analysis", "Visceral Fat Level", "Research Parameters",
        "Results Interpretation", "Impedance (ohms)"
    ):
        assert heading in text, f"Missing section: {heading}"
    assert "NOT DEVICE-VERIFIED" in text
    assert "Right Arm" in text
    assert "Left Leg" in text


def test_reference_pdf_uses_six_date_history():
    import io
    from datetime import date, timedelta
    from pypdf import PdfReader
    scans = []
    for offset in range(7):
        item = dict(VALID_SCAN)
        item["scan_date"] = (date(2026, 10, 10) + timedelta(days=offset)).isoformat()
        item["weight_lb"] = 170 + offset
        scans.append(item)
    response = client.post("/api/inbody/sheet", json={"scan": scans[-1], "history": scans[:-1]})
    assert response.status_code == 200, response.text
    text = PdfReader(io.BytesIO(response.content)).pages[0].extract_text()
    assert "10-11" in text
    assert "10-16" in text
    assert "10-10" not in text


def test_reference_pdf_missing_device_values_are_not_fabricated():
    import io
    from pypdf import PdfReader
    response = client.post("/api/inbody/sheet", json={"scan": VALID_SCAN, "history": []})
    text = PdfReader(io.BytesIO(response.content)).pages[0].extract_text()
    assert "GENERATED" in text
    assert "No device-only values are inferred." in text

def test_inbody_renderer_imports_and_builds_pdf_directly():
    from inbody_layout import build_inbody_pdf
    from app import Scan
    scan = Scan.model_validate(VALID_SCAN)
    pdf_bytes = build_inbody_pdf(scan)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1000

def test_inbody_pdf_preserves_ecw_ratio_precision():
    from inbody_layout import build_inbody_pdf
    from app import Scan
    from pypdf import PdfReader
    from io import BytesIO
    sample = dict(VALID_SCAN)
    sample.update(report_type="inbody", ecw_tbw_ratio=0.379)
    pdf = build_inbody_pdf(Scan.model_validate(sample))
    extracted = PdfReader(BytesIO(pdf)).pages[0].extract_text()
    assert "0.379" in extracted
    assert "0.4" not in extracted.split("ECW / TBW Analysis", 1)[1].split("Body Composition History", 1)[0]


def test_six_month_synthetic_report_summary_and_disclosure():
    import io
    from pypdf import PdfReader
    dates = ["2026-06-01", "2026-06-29", "2026-07-31",
             "2026-08-27", "2026-09-30", "2026-10-26"]
    weights = [292.4, 270.8, 244.6, 222.9, 205.7, 192.4]
    fats = [42.1, 38.4, 32.6, 26.1, 19.3, 13.2]
    muscles = [75.1, 76.8, 78.9, 78.5, 82.6, 85.3]
    visceral = [20, 17, 13, 10, 6, 3]
    history = []
    for i, day in enumerate(dates):
        history.append({
            **VALID_SCAN,
            "scan_date": day,
            "weight_lb": weights[i],
            "body_fat_pct": fats[i],
            "skeletal_muscle_lb": muscles[i],
            "visceral_fat_level": visceral[i],
            "ecw_tbw_ratio": [0.391, 0.389, 0.390, 0.385, 0.383, 0.379][i],
            "notes": "SYNTHETIC DEMONSTRATION DATA - not actual measurements",
            "device_model": "Synthetic demo",
        })
    response = client.post("/api/inbody/sheet", json={
        "scan": history[-1], "history": history[:-1]
    })
    assert response.status_code == 200, response.text
    reader = PdfReader(io.BytesIO(response.content))
    assert len(reader.pages) == 1
    text = reader.pages[0].extract_text()
    for expected in ("Transformation Overview", "-100.0 lb", "-28.9 pp",
                     "+10.2 lb", "-17.0", "0.379",
                     "SYNTHETIC DEMONSTRATION", "NOT REAL SCAN RESULTS"):
        assert expected in text, expected
    for day in dates:
        assert day[5:] in text
    assert "No device-only values are inferred." not in text
