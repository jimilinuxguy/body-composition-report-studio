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
