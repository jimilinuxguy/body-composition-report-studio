import csv
import io
import json
from datetime import date
from pathlib import Path
from typing import Optional, Literal
from fastapi import FastAPI, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel, Field, model_validator
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

ROOT = Path(__file__).parent
app = FastAPI(title='Body Composition Report Studio')
app.mount('/static', StaticFiles(directory=ROOT/'static'), name='static')
templates = Jinja2Templates(directory=ROOT/'templates')

class Scan(BaseModel):
    report_type: str = 'inbody'
    device_model: str = 'Generic'
    notes: str = ''
    field_sources: dict[str, Literal['measured','estimated','calculated']] = Field(default_factory=dict)
    source: str = 'estimated'
    name: str = 'Sample Client'
    scan_date: date = Field(default_factory=date.today)
    sex: str = 'unspecified'
    age: Optional[int] = Field(default=None, ge=0, le=120)
    height_in: float = Field(gt=0, le=100)
    weight_lb: float = Field(gt=0, le=1500)
    body_fat_pct: float = Field(ge=0, le=100)
    skeletal_muscle_lb: Optional[float] = Field(default=None, ge=0)
    total_body_water_lb: Optional[float] = Field(default=None, ge=0)
    bone_mineral_lb: Optional[float] = Field(default=None, ge=0)
    visceral_fat_area_cm2: Optional[float] = Field(default=None, ge=0)
    android_fat_pct: Optional[float] = Field(default=None, ge=0, le=100)
    gynoid_fat_pct: Optional[float] = Field(default=None, ge=0, le=100)
    trunk_fat_pct: Optional[float] = Field(default=None, ge=0, le=100)
    arms_fat_pct: Optional[float] = Field(default=None, ge=0, le=100)
    legs_fat_pct: Optional[float] = Field(default=None, ge=0, le=100)
    left_arm_lean_lb: Optional[float] = Field(default=None, ge=0)
    right_arm_lean_lb: Optional[float] = Field(default=None, ge=0)
    trunk_lean_lb: Optional[float] = Field(default=None, ge=0)
    left_leg_lean_lb: Optional[float] = Field(default=None, ge=0)
    right_leg_lean_lb: Optional[float] = Field(default=None, ge=0)

    protein_lb: Optional[float] = Field(default=None, ge=0)
    minerals_lb: Optional[float] = Field(default=None, ge=0)
    intracellular_water_lb: Optional[float] = Field(default=None, ge=0)
    extracellular_water_lb: Optional[float] = Field(default=None, ge=0)
    ecw_tbw_ratio: Optional[float] = Field(default=None, ge=0)
    soft_lean_mass_lb: Optional[float] = Field(default=None, ge=0)
    body_cell_mass_lb: Optional[float] = Field(default=None, ge=0)
    basal_metabolic_rate_kcal: Optional[float] = Field(default=None, ge=0)
    waist_hip_ratio: Optional[float] = Field(default=None, ge=0)
    obesity_degree_pct: Optional[float] = Field(default=None, ge=0)
    inbody_score: Optional[float] = Field(default=None, ge=0)
    target_weight_lb: Optional[float] = Field(default=None, ge=0)
    weight_control_lb: Optional[float] = Field(default=None, ge=-1500)
    fat_control_lb: Optional[float] = Field(default=None, ge=-1500)
    muscle_control_lb: Optional[float] = Field(default=None, ge=-1500)
    visceral_fat_level: Optional[float] = Field(default=None, ge=0)
    phase_angle_deg: Optional[float] = Field(default=None, ge=0)
    right_arm_lean_pct: Optional[float] = Field(default=None, ge=0)
    right_arm_fat_lb: Optional[float] = Field(default=None, ge=0)
    right_arm_fat_pct: Optional[float] = Field(default=None, ge=0)
    right_arm_ecw_ratio: Optional[float] = Field(default=None, ge=0)
    left_arm_lean_pct: Optional[float] = Field(default=None, ge=0)
    left_arm_fat_lb: Optional[float] = Field(default=None, ge=0)
    left_arm_fat_pct: Optional[float] = Field(default=None, ge=0)
    left_arm_ecw_ratio: Optional[float] = Field(default=None, ge=0)
    trunk_lean_pct: Optional[float] = Field(default=None, ge=0)
    trunk_fat_lb: Optional[float] = Field(default=None, ge=0)
    trunk_fat_pct: Optional[float] = Field(default=None, ge=0)
    trunk_ecw_ratio: Optional[float] = Field(default=None, ge=0)
    right_leg_lean_pct: Optional[float] = Field(default=None, ge=0)
    right_leg_fat_lb: Optional[float] = Field(default=None, ge=0)
    right_leg_fat_pct: Optional[float] = Field(default=None, ge=0)
    right_leg_ecw_ratio: Optional[float] = Field(default=None, ge=0)
    left_leg_lean_pct: Optional[float] = Field(default=None, ge=0)
    left_leg_fat_lb: Optional[float] = Field(default=None, ge=0)
    left_leg_fat_pct: Optional[float] = Field(default=None, ge=0)
    left_leg_ecw_ratio: Optional[float] = Field(default=None, ge=0)
    impedance_1khz_right_arm_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_1khz_left_arm_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_1khz_trunk_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_1khz_right_leg_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_1khz_left_leg_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_5khz_right_arm_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_5khz_left_arm_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_5khz_trunk_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_5khz_right_leg_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_5khz_left_leg_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_50khz_right_arm_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_50khz_left_arm_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_50khz_trunk_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_50khz_right_leg_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_50khz_left_leg_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_250khz_right_arm_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_250khz_left_arm_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_250khz_trunk_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_250khz_right_leg_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_250khz_left_leg_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_500khz_right_arm_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_500khz_left_arm_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_500khz_trunk_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_500khz_right_leg_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_500khz_left_leg_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_1000khz_right_arm_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_1000khz_left_arm_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_1000khz_trunk_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_1000khz_right_leg_ohm: Optional[float] = Field(default=None, ge=0)
    impedance_1000khz_left_leg_ohm: Optional[float] = Field(default=None, ge=0)

    @model_validator(mode='after')
    def validate_fields(self):
        if self.report_type not in ('dexa', 'inbody') or self.source not in ('measured', 'estimated'):
            raise ValueError('Invalid report type or source')
        if any(k not in type(self).model_fields or k in ('field_sources','notes','name') for k in self.field_sources):
            raise ValueError('Unknown measurement source field')
        if self.skeletal_muscle_lb is not None and self.skeletal_muscle_lb > self.weight_lb:
            raise ValueError('Muscle mass cannot exceed weight')
        return self

def metrics(s: Scan):
    fat = s.weight_lb * s.body_fat_pct / 100
    return {'fat_mass_lb': round(fat, 2), 'fat_free_mass_lb': round(s.weight_lb-fat, 2),
            'bmi': round(703*s.weight_lb/s.height_in**2, 1),
            'fat_free_mass_index': round((s.weight_lb-fat)*0.45359237/(s.height_in*0.0254)**2, 1)}

def quality_checks(s: Scan):
    warnings=[]
    if s.total_body_water_lb is not None and s.intracellular_water_lb is not None and s.extracellular_water_lb is not None:
        if abs(s.total_body_water_lb-s.intracellular_water_lb-s.extracellular_water_lb)>max(1, .02*s.total_body_water_lb):
            warnings.append('Total body water differs from intracellular + extracellular water.')
    if s.ecw_tbw_ratio is not None and s.total_body_water_lb and s.extracellular_water_lb is not None:
        if abs(s.ecw_tbw_ratio-s.extracellular_water_lb/s.total_body_water_lb)>.025:
            warnings.append('ECW/TBW ratio differs from entered extracellular and total body water.')
    if s.body_fat_pct is not None and s.body_fat_pct>65:
        warnings.append('Body fat percentage is unusually high. Verify the value and units.')
    if s.weight_lb and s.total_body_water_lb and s.total_body_water_lb>s.weight_lb:
        warnings.append('Total body water exceeds total body weight.')
    return warnings

@app.post('/api/validate')
def validate_scan(s: Scan):
    supplied=[k for k,v in s.model_dump().items() if isinstance(v,(int,float)) and v is not None]
    return {'warnings':quality_checks(s),'numeric_fields_supplied':len(supplied), 'sources':s.field_sources}

@app.get('/', response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name='index.html', context={})

@app.post('/api/report')
def report(s: Scan):
    return {'scan':s.model_dump(mode='json'), 'metrics':metrics(s), 'warnings':quality_checks(s)}

class InBodySheetRequest(BaseModel):
    scan: Scan
    history: list[Scan] = Field(default_factory=list, max_length=250)

@app.post('/api/inbody/sheet')
def inbody_sheet(req: InBodySheetRequest):
    from inbody_layout import build_inbody_pdf
    current=req.scan
    history=[s for s in req.history if s.name.strip().lower()==current.name.strip().lower() and s.scan_date!=current.scan_date]
    history.append(current)
    data=build_inbody_pdf(current,history)
    return StreamingResponse(io.BytesIO(data),media_type='application/pdf',
        headers={'Content-Disposition':'attachment; filename="inbody_generated_report.pdf"'})

@app.post('/api/pdf')
def pdf(s: Scan):
    data = create_pdf(s)
    return StreamingResponse(io.BytesIO(data), media_type='application/pdf',
        headers={'Content-Disposition':f'attachment; filename="{s.report_type}_generated_report.pdf"'})

@app.post('/api/csv')
def export_csv(s: Scan):
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=list(s.model_dump().keys()))
    w.writeheader(); w.writerow({**s.model_dump(mode='json'), 'field_sources':json.dumps(s.field_sources)})
    return StreamingResponse(iter([out.getvalue()]), media_type='text/csv', headers={'Content-Disposition':'attachment; filename="body_composition.csv"'})

@app.post('/api/import-csv')
async def import_csv(file: UploadFile = File(...)):
    try:
        content = (await file.read()).decode('utf-8-sig')
        row = next(csv.DictReader(io.StringIO(content)))
        cleaned = {k: (json.loads(v) if k=='field_sources' and v else '{}' if k=='field_sources' else '' if k in ('notes','device_model') and v=='' else None if v == '' else v) for k,v in row.items()}
        s = Scan.model_validate(cleaned)
        return s.model_dump(mode='json')
    except Exception as e:
        raise HTTPException(422, detail=f'CSV could not be imported: {e}')

def create_pdf(s: Scan) -> bytes:
    if s.report_type == 'inbody':
        from inbody_layout import build_inbody_pdf
        return build_inbody_pdf(s)
    buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=letter)
    W,H = letter
    ink = colors.HexColor('#17283a'); accent = colors.HexColor('#006d89') if s.report_type=='inbody' else colors.HexColor('#385c9a')
    muted = colors.HexColor('#66778a')
    m=metrics(s)
    def txt(x,y,t,size=10,bold=False,color=ink):
        c.setFillColor(color); c.setFont('Helvetica-Bold' if bold else 'Helvetica',size); c.drawString(x,y,str(t))
    def rule(y):
        c.setStrokeColor(colors.HexColor('#dce3e9')); c.line(40,y,W-40,y)
    def section(y,title):
        c.setFillColor(accent); c.roundRect(40,y-6,W-80,24,3,fill=1,stroke=0)
        txt(49,y+1,title,10,True,colors.white)
        return y-28
    def row(y,label,value,note=''):
        txt(49,y,label,9); txt(315,y,value,10,True); txt(440,y,note,8,color=muted); rule(y-8)
        return y-25
    c.setFillColor(accent); c.rect(0,H-13,W,13,fill=1,stroke=0)
    txt(40,H-49,'BODY COMPOSITION ANALYSIS',19,True)
    txt(40,H-68,('DEXA-STYLE' if s.report_type=='dexa' else 'INBODY-STYLE')+'  |  GENERATED REPORT',10,True,accent)
    txt(40,H-89,'Not an original device-issued scan. Values reflect user-provided data.',8,color=muted)
    rule(H-101)
    txt(40,H-120,f'Name: {s.name[:50]}',10,True)
    txt(345,H-120,f'Date: {s.scan_date}',9)
    txt(40,H-138,f'Height: {s.height_in:.1f} in     Weight: {s.weight_lb:.1f} lb',9)
    txt(345,H-138,f'Source: {s.source.upper()}',9,True,accent)
    y=H-170
    y=section(y,'BODY COMPOSITION')
    for label,val,note in [('Weight',f'{s.weight_lb:.1f} lb','Entered'),('Body Fat Percentage',f'{s.body_fat_pct:.1f}%','Entered'),('Fat Mass',f'{m["fat_mass_lb"]:.1f} lb','Calculated'),('Fat-Free Mass',f'{m["fat_free_mass_lb"]:.1f} lb','Calculated'),('Body Mass Index',f'{m["bmi"]:.1f}','Calculated')]:
        y=row(y,label,val,note)
    y-=12
    y=section(y,'REGIONAL ANALYSIS' if s.report_type=='dexa' else 'MUSCLE / WATER ANALYSIS')
    fields = ([('Bone Mineral Content',s.bone_mineral_lb,'lb'),('Android Fat',s.android_fat_pct,'%'),('Gynoid Fat',s.gynoid_fat_pct,'%'),('Trunk Fat',s.trunk_fat_pct,'%'),('Arms Fat',s.arms_fat_pct,'%'),('Legs Fat',s.legs_fat_pct,'%')] if s.report_type=='dexa' else [('Skeletal Muscle Mass',s.skeletal_muscle_lb,'lb'),('Total Body Water',s.total_body_water_lb,'lb'),('Left Arm Lean',s.left_arm_lean_lb,'lb'),('Right Arm Lean',s.right_arm_lean_lb,'lb'),('Trunk Lean',s.trunk_lean_lb,'lb'),('Left Leg Lean',s.left_leg_lean_lb,'lb'),('Right Leg Lean',s.right_leg_lean_lb,'lb')])
    for label,value,unit in fields:
        y=row(y,label,f'{value:.1f} {unit}' if value is not None else 'Not provided','Entered' if value is not None else '')
    y-=9
    if y>125:
        y=section(y,'ADDITIONAL MEASUREMENTS')
        y=row(y,'Visceral Fat Area',f'{s.visceral_fat_area_cm2:.1f} cm2' if s.visceral_fat_area_cm2 is not None else 'Not provided','Entered' if s.visceral_fat_area_cm2 is not None else '')
    c.setFillColor(colors.HexColor('#f0f4f7')); c.roundRect(40,52,W-80,45,4,fill=1,stroke=0)
    txt(50,78,'GENERATED / NOT DEVICE-VERIFIED',9,True,accent)
    txt(50,64,'Calculated values are derived from entered measurements. Missing device metrics are not inferred.',7.4)
    txt(40,34,'For tracking and visualization only. Not a clinical diagnostic document.',8,color=muted)
    c.save(); return buf.getvalue()

class HistoryRequest(BaseModel):
    scans: list[Scan] = Field(min_length=1, max_length=250)
    report_type: str = 'inbody'

    @model_validator(mode='after')
    def check(self):
        if self.report_type not in ('dexa','inbody'):
            raise ValueError('Unknown report type')
        if len({s.name.strip().lower() for s in self.scans}) != 1:
            raise ValueError('All entries must belong to the same person')
        if len({s.scan_date for s in self.scans}) != len(self.scans):
            raise ValueError('Each entry must have a unique date')
        return self

@app.post('/api/history')
def history(req: HistoryRequest):
    ordered=sorted(req.scans,key=lambda s:s.scan_date)
    return {'entries':[{'scan':s.model_dump(mode='json'),'metrics':metrics(s)} for s in ordered], 'count':len(ordered)}

@app.post('/api/history/csv')
def history_csv(req: HistoryRequest):
    out=io.StringIO(); fields=list(Scan.model_fields.keys()); writer=csv.DictWriter(out,fieldnames=fields)
    writer.writeheader()
    for s in sorted(req.scans,key=lambda x:x.scan_date):writer.writerow({**s.model_dump(mode='json'), 'field_sources':json.dumps(s.field_sources)})
    return StreamingResponse(iter([out.getvalue()]),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="bodycomp_history.csv"'})

@app.post('/api/history/pdf')
def history_pdf(req: HistoryRequest):
    scans=sorted(req.scans,key=lambda s:s.scan_date)
    buf=io.BytesIO(); c=canvas.Canvas(buf,pagesize=letter); W,H=letter
    accent=colors.HexColor('#385c9a' if req.report_type=='dexa' else '#006d89')
    ink=colors.HexColor('#243247')
    def text(x,y,value,size=9,bold=False):
        c.setFillColor(ink);c.setFont('Helvetica-Bold' if bold else 'Helvetica',size);c.drawString(x,y,str(value))
    def header(title):
        c.setFillColor(accent);c.rect(0,H-12,W,12,fill=1,stroke=0)
        text(36,H-46,title,17,True)
        text(36,H-65,'GENERATED REPORT - NOT DEVICE-VERIFIED',10,True)
        text(36,H-84,f'Client: {scans[0].name[:48]}  |  {req.report_type.upper()}-style  |  {len(scans)} dated entries')
        text(36,38,'User-entered measurements and derived values. Not an original device scan.',8)
    def page_table(title,columns,records):
        header(title); y=H-112
        colwidth=(W-72)/len(columns)
        c.setFillColor(accent);c.rect(36,y-8,W-72,23,fill=1,stroke=0)
        c.setFillColor(colors.white);c.setFont('Helvetica-Bold',7)
        for i,col in enumerate(columns):c.drawString(40+i*colwidth,y,col[:21])
        y-=30
        for record in records:
            if y<68:
                c.showPage();header(title+' (continued)');y=H-115
            for i,val in enumerate(record):text(40+i*colwidth,y,str(val)[:22],7.6)
            c.setStrokeColor(colors.HexColor('#dfe5eb'));c.line(36,y-6,W-36,y-6)
            y-=22
        c.showPage()
    def fmt(v):return '' if v is None else f'{v:.1f}'
    summary=[]
    for s in scans:
        m=metrics(s)
        summary.append([str(s.scan_date),fmt(s.weight_lb),fmt(s.body_fat_pct),fmt(m['fat_mass_lb']),fmt(m['fat_free_mass_lb']),fmt(m['bmi'])])
    page_table('BODY COMPOSITION HISTORY',['Date','Weight lb','Body fat %','Fat mass lb','Fat-free lb','BMI'],summary)
    header('MEASUREMENT TRENDS')
    plots=[('Weight (lb)',[s.weight_lb for s in scans]),('Body fat (%)',[s.body_fat_pct for s in scans]),('Fat mass (lb)',[metrics(s)['fat_mass_lb'] for s in scans]),('Fat-free mass (lb)',[metrics(s)['fat_free_mass_lb'] for s in scans])]
    for j,(label,values) in enumerate(plots):
        top=H-122-j*148
        text(42,top,label,10,True)
        left,right=70,W-60;bottom=top-108;charttop=top-20
        c.setStrokeColor(colors.HexColor('#c9d3de'));c.line(left,bottom,right,bottom);c.line(left,bottom,left,charttop)
        lo=min(values);hi=max(values);span=max(hi-lo,1)
        c.setStrokeColor(accent);c.setLineWidth(2)
        pts=[]
        for i,v in enumerate(values):
            x=left+(right-left)*(i/(len(values)-1) if len(values)>1 else .5)
            y=bottom+8+(v-lo)/span*(charttop-bottom-16)
            pts.append((x,y))
        for a,b in zip(pts,pts[1:]):c.line(a[0],a[1],b[0],b[1])
        for i,(x,y) in enumerate(pts):
            c.setFillColor(accent);c.circle(x,y,2.7,fill=1,stroke=0)
            if len(pts)<=12 or i in (0,len(pts)-1):
                text(max(left,x-10),y+6,fmt(values[i]),7)
                text(max(left,x-17),bottom-12,str(scans[i].scan_date)[5:],6)
    c.showPage()
    extra_keys=([('bone_mineral_lb','Bone lb'),('android_fat_pct','Android %'),('gynoid_fat_pct','Gynoid %'),('trunk_fat_pct','Trunk %'),('arms_fat_pct','Arms %'),('legs_fat_pct','Legs %')] if req.report_type=='dexa' else [('skeletal_muscle_lb','Muscle lb'),('total_body_water_lb','Water lb'),('left_arm_lean_lb','L arm lb'),('right_arm_lean_lb','R arm lb'),('left_leg_lean_lb','L leg lb'),('right_leg_lean_lb','R leg lb')])
    page_table('DEVICE-SPECIFIC HISTORY',['Date']+[label for _,label in extra_keys],[[str(s.scan_date)]+[fmt(getattr(s,k)) for k,_ in extra_keys] for s in scans])
    # Full instrument-specific measurement archive, including all optional fields.
    instrument_fields=[k for k in Scan.model_fields if k not in ('report_type','source','name','scan_date','sex','age','height_in','weight_lb','body_fat_pct','field_sources','notes','device_model')]
    for scan in scans:
        rows=[]
        for key in instrument_fields:
            value=getattr(scan,key)
            rows.append([key.replace('_',' ').title(), 'Not provided' if value is None else f'{value:g} ({scan.field_sources.get(key, scan.source)})'])
        page_table(f'FULL MEASUREMENT RECORD - {scan.scan_date}', ['Measurement','Recorded value'], rows)
    for scan in scans:
        warnings=quality_checks(scan)
        if warnings:
            page_table(f'REVIEW WARNINGS - {scan.scan_date}', ['Check'], [[w] for w in warnings])
    c.save();return StreamingResponse(io.BytesIO(buf.getvalue()),media_type='application/pdf',headers={'Content-Disposition':'attachment; filename="bodycomp_longitudinal_report.pdf"'})

@app.post('/api/history/import-csv')
async def history_import(file: UploadFile=File(...)):
    try:
        content=(await file.read()).decode('utf-8-sig')
        records=list(csv.DictReader(io.StringIO(content)))
        if not records or len(records)>250:raise ValueError('CSV must have 1 to 250 entries')
        scans=[Scan.model_validate({k:(json.loads(v) if k=='field_sources' and v else '{}' if k=='field_sources' else '' if k in ('notes','device_model') and v=='' else None if v=='' else v) for k,v in row.items() if k in Scan.model_fields}) for row in records]
        HistoryRequest(scans=scans)
        return {'scans':[s.model_dump(mode='json') for s in sorted(scans,key=lambda x:x.scan_date)]}
    except Exception as exc:raise HTTPException(422,detail=str(exc))
