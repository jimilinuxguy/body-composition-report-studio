from fastapi.testclient import TestClient
from app import app
client=TestClient(app)
scan={'report_type':'dexa','source':'estimated','name':'Test','scan_date':'2026-10-25','height_in':71,'weight_lb':170,'body_fat_pct':15}
def test_metrics():
    r=client.post('/api/report',json=scan)
    assert r.status_code==200
    assert r.json()['metrics']['fat_mass_lb']==25.5
def test_pdf():
    r=client.post('/api/pdf',json=scan)
    assert r.status_code==200 and r.content.startswith(b'%PDF')
def test_csv():
    r=client.post('/api/csv',json=scan)
    assert r.status_code==200 and 'body_fat_pct' in r.text

def test_provenance_and_quality():
    payload={**scan,'report_type':'inbody','field_sources':{'skeletal_muscle_lb':'measured'},'skeletal_muscle_lb':80,'total_body_water_lb':100,'intracellular_water_lb':40,'extracellular_water_lb':40}
    r=client.post('/api/validate',json=payload)
    assert r.status_code==200 and r.json()['warnings']
    assert r.json()['sources']['skeletal_muscle_lb']=='measured'

def test_csv_provenance_roundtrip():
    payload={**scan,'field_sources':{'skeletal_muscle_lb':'estimated'}}
    exported=client.post('/api/csv',json=payload)
    assert exported.status_code==200
    imported=client.post('/api/import-csv',files={'file':('scans.csv',exported.content,'text/csv')})
    assert imported.status_code==200
    assert imported.json()['field_sources']['skeletal_muscle_lb']=='estimated'

def test_history_pdf_with_provenance():
    payload={**scan,'field_sources':{'skeletal_muscle_lb':'measured'}}
    r=client.post('/api/history/pdf',json={'scans':[payload],'report_type':'dexa'})
    assert r.status_code==200 and r.content.startswith(b'%PDF')
