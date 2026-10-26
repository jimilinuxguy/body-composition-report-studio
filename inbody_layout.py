"""Reference-inspired InBody-style report. Generated, not device-issued."""
import io
import json
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

W,H=A4
RED=colors.HexColor("#873e46")
INK=colors.HexColor("#242729")
GRAY=colors.HexColor("#718087")
PALE=colors.HexColor("#e6ebed")
BAR=colors.HexColor("#555e62")
MARGIN=32
LEFT=352
RIGHT_X=395
RIGHT_W=185

def report_config():
    path=Path(__file__).parent/"data"/"report_config.json"
    defaults={"show_generated_header_notice":True,"show_generated_footer_notice":True,"show_tracking_footer":True,"show_segmental_disclaimer":True,"show_device_values_disclaimer":True}
    if not path.exists():
        return defaults
    config=json.loads(path.read_text(encoding="utf-8"))
    for key in defaults:
        if key in config and not isinstance(config[key],bool):
            raise ValueError(f"{key} must be true or false")
    return {**defaults,**config}


def build_inbody_pdf(scan, history=None):
    """Draw the same printable sheet used by the browser preview."""
    full_history=sorted(history or [scan],key=lambda x:x.scan_date)
    history=full_history[-6:]
    # The six most recent scans drive the charts and recent-period deltas;
    # the complete record remains available for lifetime comparisons.
    is_synthetic=any("synthetic" in str(getattr(h,"notes","")).lower() or "synthetic" in str(getattr(h,"device_model","")).lower() for h in history)
    config=report_config()
    out=io.BytesIO()
    c=canvas.Canvas(out,pagesize=A4,pageCompression=0)
    c.setTitle("Generated InBody-style body composition report")
    def text(x,y,s,size=8,bold=False,color=INK):
        c.setFont("Helvetica-Bold" if bold else "Helvetica",size)
        c.setFillColor(color)
        c.drawString(x,y,str(s))
    def line(x1,y1,x2,y2,color=PALE,width=.6):
        c.setStrokeColor(color);c.setLineWidth(width);c.line(x1,y1,x2,y2)
    def value(v,d=1):
        return "—" if v is None else f"{v:.{d}f}"
    def section(x,y,w,title):
        text(x,y,title,11,True)
        c.setFillColor(PALE)
        c.rect(x,y-11,w,4,stroke=0,fill=1)
        line(x,y-12,x+w,y-12,GRAY,.5)
        return y-19
    def bar(x,y,w,number,lo,hi):
        c.setFillColor(PALE);c.rect(x,y-3,w,6,stroke=0,fill=1)
        for tick in range(1,6):
            xx=x+w*tick/6
            line(xx,y-4,xx,y+4,colors.white,.6)
        if number is not None:
            frac=max(0,min(1,(number-lo)/(hi-lo)))
            c.setFillColor(BAR);c.rect(x,y-3,max(2,w*frac),6,stroke=0,fill=1)
    def row(x,y,label,v,unit="",width=LEFT):
        text(x+3,y,label,7.6)
        text(x+width-76,y,value(v),8.2,True)
        text(x+width-31,y,unit,7,color=GRAY)
        line(x,y-5,x+width,y-5)
        return y-14
    def metric(x,y,label,v,unit,lo,hi,decimals=1):
        text(x+3,y,label,7.6,True)
        bar(x+107,y+1,155,v,lo,hi)
        text(x+275,y,value(v,decimals),8.6,True)
        text(x+317,y,unit,7,color=GRAY)
        line(x,y-7,x+LEFT,y-7)
        return y-21
    def small_row(x,y,label,v):
        text(x+2,y,label,7.5)
        text(x+125,y,value(v),8,True)
        line(x,y-5,x+RIGHT_W,y-5)
        return y-18
    def regional(x,y,title,kind):
        y=section(x,y,LEFT,title)
        for label,key in [("Right Arm","right_arm"),("Left Arm","left_arm"),("Trunk","trunk"),("Right Leg","right_leg"),("Left Leg","left_leg")]:
            amount=getattr(scan,f"{key}_{kind}_lb",None)
            pct=getattr(scan,f"{key}_{kind}_pct",None)
            text(x+3,y,label,7.6,True)
            text(x+84,y,value(amount,2)+" lb" if amount is not None else "—",7.7)
            bar(x+151,y+1,122,pct,50,150)
            text(x+285,y,(value(pct)+"%" if pct is not None else "N/A"),7.5,color=GRAY if pct is None else INK)
            line(x,y-7,x+LEFT,y-7)
            y-=19
        return y-6
    # Header and identity
    text(MARGIN,H-39,"InBody",27,True,RED)
    text(MARGIN+103,H-36,"STYLE BODY COMPOSITION REPORT",9,True,GRAY)
    line(MARGIN,H-49,W-MARGIN,H-49,RED,1.7)
    text(MARGIN,H-65,"Name / ID",7,color=GRAY)
    text(MARGIN,H-77,scan.name[:30],9,True)
    text(185,H-65,"Height",7,color=GRAY)
    text(185,H-77,f"{scan.height_in:.1f} in",9)
    text(256,H-65,"Age",7,color=GRAY)
    text(256,H-77,value(scan.age,0),9)
    text(304,H-65,"Sex",7,color=GRAY)
    text(304,H-77,str(scan.sex).title(),9)
    text(386,H-65,"Test date",7,color=GRAY)
    text(386,H-77,str(scan.scan_date),9)
    status=("SYNTHETIC DEMONSTRATION - NOT REAL MEASUREMENTS" if is_synthetic else "GENERATED / NOT DEVICE-VERIFIED - Entered or calculated values")
    if is_synthetic or config["show_generated_header_notice"]:
        text(MARGIN,H-92,status,7,True,RED)
    # Left: stacked analytical sections
    x=MARGIN;y=H-115
    y=section(x,y,LEFT,"Body Composition Analysis")
    fat=scan.weight_lb*scan.body_fat_pct/100
    lean=scan.weight_lb-fat
    for label,v,u in [
        ("Intracellular Water",scan.intracellular_water_lb,"lb"),
        ("Extracellular Water",scan.extracellular_water_lb,"lb"),
        ("Total Body Water",scan.total_body_water_lb,"lb"),
        ("Protein",scan.protein_lb,"lb"),
        ("Minerals",scan.minerals_lb,"lb"),
        ("Lean Body Mass",lean,"lb*"),
        ("Body Fat Mass",fat,"lb*"),
        ("Weight",scan.weight_lb,"lb")]:
        y=row(x,y,label,v,u)
    text(x+3,y+3,"* Calculated from entered weight and body fat %",6.2,color=GRAY)
    y-=14
    y=section(x,y,LEFT,"Muscle-Fat Analysis")
    y=metric(x,y,"Weight",scan.weight_lb,"lb",75,350)
    y=metric(x,y,"Skeletal Muscle Mass",scan.skeletal_muscle_lb,"lb",30,150)
    y=metric(x,y,"Body Fat Mass",fat,"lb",0,140)
    y-=6
    y=section(x,y,LEFT,"Obesity Analysis")
    bmi=703*scan.weight_lb/scan.height_in**2
    y=metric(x,y,"BMI",bmi,"kg/m²",10,50)
    y=metric(x,y,"Percent Body Fat",scan.body_fat_pct,"%",0,50)
    y-=8
    y=regional(x,y,"Segmental Lean Analysis","lean")
    y=section(x,y,LEFT,"ECW / TBW Analysis")
    y=metric(x,y,"ECW / TBW",scan.ecw_tbw_ratio,"",.32,.45,3)
    y-=5
    y=section(x,y,LEFT,"Body Composition History")
    # A shared date header and four self-contained chart bands.
    # All labels, values and plots for a metric stay within its own band.
    hx=x+112
    cw=39
    for i,h in enumerate(history):
        date_label=str(h.scan_date)[5:]
        center_x=hx+11+i*cw
        text(center_x-pdfmetrics.stringWidth(date_label,"Helvetica",6.8)/2,y,date_label,6.8,color=GRAY)
    y-=12
    chart_rows=[
        ("Weight (lb)",lambda z:z.weight_lb,1),
        ("SMM (lb)",lambda z:z.skeletal_muscle_lb,1),
        ("PBF (%)",lambda z:z.body_fat_pct,1),
        ("ECW/TBW",lambda z:z.ecw_tbw_ratio,3),
    ]
    band_h=36
    for row_index,(label,fn,decimals) in enumerate(chart_rows):
        top=y
        bottom=top-band_h
        if row_index%2==0:
            c.setFillColor(colors.HexColor("#f4f6f7"))
            c.rect(x,bottom,LEFT,band_h,stroke=0,fill=1)
        # Label is centered vertically against its *own* plot, never the next row.
        text(x+3,bottom+11,label,8,True)
        values=[fn(h) for h in history]
        numeric=[v for v in values if v is not None]
        low=min(numeric) if numeric else 0
        high=max(numeric) if numeric else 1
        # Give small changes visual context rather than filling the plot height.
        if label=="ECW/TBW" and numeric and .36<=low<=high<=.40:
            low,high=.36,.40
        else:
            pad=max((high-low)*.25, .004 if label=="ECW/TBW" else .5)
            low-=pad
            high+=pad
        span=max(high-low,.001)
        # Value labels occupy the top of the band; plotted points occupy
        # the lower half, with 4 pt minimum clearance to the next band.
        points=[]
        for i,v in enumerate(values):
            px=hx+11+i*cw
            if v is not None:
                value_label=value(v,decimals)
                text(px-pdfmetrics.stringWidth(value_label,"Helvetica",6.8)/2,top-10,value_label,6.8)
                py=bottom+6+11*(v-low)/span
                points.append((px,py))
        for p,q in zip(points,points[1:]):
            line(*p,*q,RED,1)
        for px,py in points:
            c.setFillColor(RED)
            c.circle(px,py,1.7,stroke=0,fill=1)
        line(x,bottom,x+LEFT,bottom,PALE,.7)
        y=bottom
    # Right side
    rx=RIGHT_X;ry=H-115
    ry=section(rx,ry,RIGHT_W,"Body Fat / Lean Control")
    for label,v in [("Weight Control",scan.weight_control_lb),("Fat Control",scan.fat_control_lb),("Muscle Control",scan.muscle_control_lb)]:
        ry=small_row(rx,ry,label,v)
    if any(v is not None for v in (scan.weight_control_lb,scan.fat_control_lb,scan.muscle_control_lb)):
        text(rx+2,ry+2,"0.0 = target achieved; not historical change",6.2,color=GRAY)
    ry-=10
    ry=section(rx,ry,RIGHT_W,"Segmental Fat Analysis")
    for label,key in [("Right Arm","right_arm"),("Left Arm","left_arm"),("Trunk","trunk"),("Right Leg","right_leg"),("Left Leg","left_leg")]:
        v=getattr(scan,key+"_fat_lb",None);pct=getattr(scan,key+"_fat_pct",None)
        text(rx+2,ry,label,7.3)
        text(rx+80,ry,value(v,2)+" lb" if v is not None else "—",7.1)
        if pct is not None:
            bar(rx+127,ry+1,38,pct,0,150)
        else:
            text(rx+131,ry,"N/A",6.2,color=GRAY)
        ry-=20
    ry-=6
    ry=section(rx,ry,RIGHT_W,"Visceral Fat Level")
    ry=small_row(rx,ry,"Level",scan.visceral_fat_level)
    bar(rx+7,ry+2,165,scan.visceral_fat_level,0,20)
    ry-=20
    ry=section(rx,ry,RIGHT_W,"Research Parameters")
    for label,v in [("Basal Metabolic Rate",scan.basal_metabolic_rate_kcal),("InBody Score",scan.inbody_score),("Waist / Hip Ratio",scan.waist_hip_ratio),("Phase Angle",scan.phase_angle_deg)]:
        ry=small_row(rx,ry,label,v)
    ry-=8
    ry=section(rx,ry,RIGHT_W,"Results Interpretation")
    interpretation=[
        "Body composition includes fat mass",
        "and fat-free mass.",
        "BMI is derived from weight and height.",
    ]
    if is_synthetic or config.get("show_segmental_disclaimer",True):
        interpretation.extend([
            "Segmental values are illustrative" if is_synthetic else "Segmental values are shown only",
            "and not device-measured." if is_synthetic else "when supplied by the user.",
        ])
    if is_synthetic or config.get("show_device_values_disclaimer",True):
        interpretation.append("Device-only fields may be unavailable." if is_synthetic else "No device-only values are inferred.")
    for msg in interpretation:
        text(rx+2,ry,msg,7,color=GRAY)
        ry-=12
    ry-=8
    ry=section(rx,ry,RIGHT_W,"Impedance (ohms)")
    keys=[("RA","right_arm"),("LA","left_arm"),("TR","trunk"),("RL","right_leg"),("LL","left_leg")]
    for i,(abbr,_) in enumerate(keys):text(rx+44+i*28,ry,abbr,6.5,True)
    ry-=14
    for freq in (5,50,500):
        text(rx+2,ry,str(freq)+" kHz",6.6)
        for i,(_,key) in enumerate(keys):
            v=getattr(scan,f"impedance_{freq}khz_{key}_ohm",None)
            text(rx+42+i*28,ry,value(v,0),6.3)
        ry-=15
    # Full transformation and recent six-date window are intentionally separate.
    if len(history)>1:
        first,last=history[0],history[-1]
        original=full_history[0]
        ry-=18
        ry=section(rx,ry,RIGHT_W,"Transformation Overview")
        text(rx+2,ry,"Lifetime: "+str(original.scan_date)[:7]+" to "+str(last.scan_date)[:7],6.7,color=GRAY)
        text(rx+2,ry-10,"Recent: "+str(first.scan_date)[:7]+" to "+str(last.scan_date)[:7],6.7,color=GRAY)
        ry-=18
        def change_row(label,begin,end,unit="",digits=1):
            nonlocal ry
            display="N/A" if begin is None or end is None else f"{end-begin:+.{digits}f}{unit}"
            text(rx+2,ry,label,7.1)
            text(rx+119,ry,display,8,True)
            line(rx,ry-5,rx+RIGHT_W,ry-5)
            ry-=18
        change_row("Total weight",original.weight_lb,last.weight_lb," lb")
        change_row("Recent weight",first.weight_lb,last.weight_lb," lb")
        change_row("Recent body fat",first.body_fat_pct,last.body_fat_pct," pp")
        change_row("Recent muscle",first.skeletal_muscle_lb,last.skeletal_muscle_lb," lb")
        if is_synthetic:
            text(rx+2,ry-1,"Fictional demo trends; not measured.",6.5,color=RED)
    line(MARGIN,43,W-MARGIN,43,RED,1)
    if is_synthetic or config["show_generated_footer_notice"]:
        text(MARGIN,30,("SYNTHETIC DEMO - NOT REAL SCAN RESULTS" if is_synthetic else "GENERATED REPORT - NOT AN ORIGINAL INBODY RESULT SHEET"),7,True,RED)
    if is_synthetic or config.get("show_tracking_footer",True):
        text(MARGIN,19,("Fictional software demonstration - not for medical use." if is_synthetic else "For personal tracking; not a diagnostic or device-verified measurement."),6.8,color=GRAY)
    c.save()
    return out.getvalue()
