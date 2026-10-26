"""Reference-inspired InBody-style report. Generated, not device-issued."""
import io
import json
from datetime import date
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
    defaults={"show_generated_header_notice":True,"show_generated_footer_notice":True,"show_tracking_footer":True,"show_calculated_values_note":True,"show_maintenance_control_baseline":True,"show_segmental_disclaimer":True,"show_device_values_disclaimer":True}
    if not path.exists():
        return {**defaults, "report_branding": "inbody", "history_mode": "full", "history_recent_count": 6, "history_date_format": "month_year"}
    config=json.loads(path.read_text(encoding="utf-8"))
    for key in defaults:
        if key in config and not isinstance(config[key],bool):
            raise ValueError(f"{key} must be true or false")
    branding = config.get("report_branding", "inbody")
    if branding not in ("inbody", "generic"):
        raise ValueError("report_branding must be inbody or generic")
    history_mode = config.get("history_mode", "full")
    if history_mode not in ("full", "recent"):
        raise ValueError("history_mode must be full or recent")
    recent_count = config.get("history_recent_count", 6)
    if type(recent_count) is not int or not 2 <= recent_count <= 25:
        raise ValueError("history_recent_count must be an integer from 2 to 25")
    date_format=config.get("history_date_format", "month_year")
    if date_format not in ("month_year", "us_short", "us_full"):
        raise ValueError("history_date_format must be month_year, us_short or us_full")
    return {**defaults, **config, "history_date_format": date_format, "report_branding": branding,
            "history_mode": history_mode, "history_recent_count": recent_count}


def build_inbody_pdf(scan, history=None):
    """Draw the same printable sheet used by the browser preview."""
    full_history=sorted(history or [scan],key=lambda x:x.scan_date)
    # Recent comparisons always use six scans; the chart window is configurable.
    recent_history=full_history[-6:]
    is_synthetic=("synthetic" in str(getattr(scan,"notes","")).lower() or "synthetic" in str(getattr(scan,"device_model","")).lower())
    config=report_config()
    history=(full_history if config.get("history_mode", "full") == "full"
             else full_history[-config.get("history_recent_count", 6):])
    out=io.BytesIO()
    c=canvas.Canvas(out,pagesize=A4,pageCompression=0)
    branding = config.get("report_branding", "inbody")
    c.setTitle("InBody Style Body Composition Report" if branding == "inbody" else "Body Composition | Personal Progress Report")
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
    if branding == "inbody":
        text(MARGIN,H-39,"InBody",27,True,RED)
        text(MARGIN+103,H-36,"STYLE BODY COMPOSITION REPORT",9,True,GRAY)
    else:
        text(MARGIN,H-39,"BODY COMPOSITION",20,True,RED)
        text(MARGIN+231,H-36,"PERSONAL PROGRESS REPORT",8,True,GRAY)
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
    if config["show_generated_header_notice"]:
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
        ("Lean Body Mass",lean,"lb*" if config.get("show_calculated_values_note",True) else "lb"),
        ("Body Fat Mass",fat,"lb*" if config.get("show_calculated_values_note",True) else "lb"),
        ("Weight",scan.weight_lb,"lb")]:
        y=row(x,y,label,v,u)
    if config.get("show_calculated_values_note",True):
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
    # Right side
    rx=RIGHT_X;ry=H-115
    ry=section(rx,ry,RIGHT_W,"Body Fat / Lean Control")
    # Use a clearly labelled zero-change maintenance baseline when no
    # control targets were supplied. This is not a recommended target.
    explicit_goal=any(v is not None for v in (
        scan.target_weight_lb,scan.weight_control_lb,
        scan.fat_control_lb,scan.muscle_control_lb))
    maintenance=not explicit_goal and config.get("show_maintenance_control_baseline",True)
    weight_control=scan.weight_control_lb
    if weight_control is None and scan.target_weight_lb is not None:
        weight_control=scan.target_weight_lb-scan.weight_lb
    muscle_control=scan.muscle_control_lb
    fat_control=scan.fat_control_lb
    if maintenance:
        weight_control=fat_control=muscle_control=0.0
    elif fat_control is None and weight_control is not None and muscle_control is not None:
        fat_control=weight_control-muscle_control
    for label,v in [("Weight Control",weight_control),("Fat Control",fat_control),("Muscle Control",muscle_control)]:
        ry=small_row(rx,ry,label,v)
    if maintenance:
        text(rx+2,ry+2,"Maintenance baseline; no goal set",6.2,color=GRAY)
    elif explicit_goal:
        text(rx+2,ry+2,"User targets; + gain / - loss (lb)",6.2,color=GRAY)
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
    text(rx+7,ry-10,"0",6.7,color=GRAY)
    text(rx+RIGHT_W-15,ry-10,"20",6.7,color=GRAY)
    ry-=26
    ry=section(rx,ry,RIGHT_W,"Research Parameters")
    research=[
        ("Basal Metabolic Rate", None if scan.basal_metabolic_rate_kcal is None else f"{scan.basal_metabolic_rate_kcal:,.0f} kcal/day"),
        ("InBody Score", None if scan.inbody_score is None else f"{scan.inbody_score:.0f} / 100"),
        ("Waist / Hip Ratio", None if scan.waist_hip_ratio is None else f"{scan.waist_hip_ratio:.2f}"),
        ("Phase Angle", None if scan.phase_angle_deg is None else f"{scan.phase_angle_deg:.1f} deg"),
    ]
    for label,display in research:
        text(rx+2,ry,label,7.3)
        if display is not None:
            c.setFont("Helvetica-Bold",7.5)
            c.setFillColor(INK)
            c.drawRightString(rx+RIGHT_W-2,ry,display)
        else:
            text(rx+RIGHT_W-22,ry,"—",7.5)
        line(rx,ry-5,rx+RIGHT_W,ry-5)
        ry-=18
    # Full transformation and recent six-date window are intentionally separate.
    if len(recent_history)>1:
        first,last=recent_history[0],recent_history[-1]
        original=full_history[0]
        ry-=4
        ry=section(rx,ry,RIGHT_W,"Transformation Overview")
        text(rx+2,ry,"Lifetime: "+str(original.scan_date)[:7]+" to "+str(last.scan_date)[:7],6.7,color=GRAY)
        text(rx+2,ry-10,"Recent: "+str(first.scan_date)[:7]+" to "+str(last.scan_date)[:7],6.7,color=GRAY)
        ry-=14
        def change_row(label,begin,end,unit="",digits=1):
            nonlocal ry
            display="N/A" if begin is None or end is None else f"{end-begin:+.{digits}f}{unit}"
            text(rx+2,ry,label,7.1)
            c.setFont("Helvetica-Bold",9 if label=="Total weight" else 8)
            c.setFillColor(RED if label=="Total weight" else INK)
            c.drawRightString(rx+RIGHT_W-3,ry,display)
            line(rx,ry-5,rx+RIGHT_W,ry-5)
            ry-=13
        # Make the lifetime result the visual anchor of the summary.
        if original.weight_lb is not None and last.weight_lb is not None:
            lifetime_delta=last.weight_lb-original.weight_lb
            c.setFillColor(colors.HexColor("#f5f0f1"))
            c.roundRect(rx,ry-35,RIGHT_W,31,4,stroke=0,fill=1)
            text(rx+8,ry-15,"Total weight",7,True,GRAY)
            c.setFont("Helvetica-Bold",15)
            c.setFillColor(RED)
            c.drawRightString(rx+RIGHT_W-8,ry-30,f"{lifetime_delta:+.1f} lb")
            ry-=40
        else:
            change_row("Total weight",original.weight_lb,last.weight_lb," lb")
        change_row("Recent weight",first.weight_lb,last.weight_lb," lb")
        change_row("Recent body fat",first.body_fat_pct,last.body_fat_pct," pp")
        change_row("Recent muscle",first.skeletal_muscle_lb,last.skeletal_muscle_lb," lb")
    # Full-width history replaces the removed interpretation/impedance blocks.
    # Keep all dated measurements visible, including densely spaced recent scans.
    # Reclaim unused separation above the history for a taller weight trend.
    y=min(y,ry)+2
    chart_width=W-2*MARGIN
    y=section(MARGIN,y,chart_width,"Body Composition History")
    plot_left=MARGIN+79
    plot_right=W-MARGIN-9
    scan_dates=[date.fromisoformat(str(h.scan_date)) for h in history]
    first_day=min(d.toordinal() for d in scan_dates)
    elapsed=max(1,max(d.toordinal() for d in scan_dates)-first_day)
    full_timeline=config.get("history_mode","full")=="full"
    positions=[plot_left+(d.toordinal()-first_day)/elapsed*(plot_right-plot_left)
               if full_timeline else plot_left+i*(plot_right-plot_left)/max(1,len(history)-1)
               for i,d in enumerate(scan_dates)]
    date_format=config.get("history_date_format","month_year")
    def date_label(d):
        if date_format=="us_full":
            return f"{d.month:02d}/{d.day:02d}/{d.year}"
        if date_format=="us_short":
            return f"{d.month}/{d.day}/{str(d.year)[2:]}"
        return f"{d.strftime('%b')} {d.year}"
    labels=[date_label(d) for d in scan_dates]
    # Allocate labels to non-overlapping lanes instead of silently omitting scans.
    # Full dates and values remain available even when measurements cluster.
    date_lanes=[float("-inf")]*3
    date_positions=[]
    for i,label in enumerate(labels):
        width=pdfmetrics.stringWidth(label,"Helvetica",6.3)
        desired=positions[i]
        best=None
        for lane in range(len(date_lanes)):
            center=max(desired,date_lanes[lane]+width/2+3)
            center=min(center,plot_right-width/2)
            left=center-width/2
            if left>=date_lanes[lane]+3 and center+width/2<=plot_right+.01:
                cost=abs(center-desired)+lane*1.2
                if best is None or cost<best[0]:
                    best=(cost,lane,center)
        if best is None:
            # Dense histories still plot every point; date labels use a compact
            # indexed key when four lanes cannot accommodate them legibly.
            best=(0,i%len(date_lanes),desired)
        _,lane,center=best
        date_lanes[lane]=center+width/2
        date_positions.append((lane,center))
        text(center-width/2,y-lane*8,label,6.3,color=GRAY)
    y-=24
    chart_rows=[
        ("Weight (lb)",lambda z:z.weight_lb,1),
        ("SMM (lb)",lambda z:z.skeletal_muscle_lb,1),
        ("PBF (%)",lambda z:z.body_fat_pct,1),
        ("ECW/TBW",lambda z:z.ecw_tbw_ratio,3),
    ]
    # Weight gets a substantially taller plot; secondary metrics stay compact.
    # The entire chart remains within the existing one-page footer boundary.
    available=max(0,y-57)
    secondary_h=24
    weight_h=min(53,max(28,available-3*secondary_h))
    for row_index,(label,fn,decimals) in enumerate(chart_rows):
        band_h=weight_h if row_index==0 else secondary_h
        top=y
        bottom=top-band_h
        if row_index%2==0:
            c.setFillColor(colors.HexColor("#f4f6f7"))
            c.rect(MARGIN,bottom,chart_width,band_h,stroke=0,fill=1)
        # Subtle date-aligned guides behind the plotted values.
        c.saveState()
        c.setStrokeColor(colors.HexColor("#d6dce0"))
        c.setLineWidth(0.35)
        c.setDash(1.3,2.8)
        for px in positions:
            c.line(px,bottom+2,px,top-2)
        c.restoreState()
        text(MARGIN+3,bottom+band_h*.45,label,7.8,True)
        values=[fn(h) for h in history]
        numeric=[v for v in values if v is not None]
        low=min(numeric) if numeric else 0
        high=max(numeric) if numeric else 1
        # Small symmetric padding makes the full observed change visible.
        pad=max((high-low)*.04,.0002 if label=="ECW/TBW" else .2)
        low-=pad
        high+=pad
        span=max(high-low,.001)
        points=[]
        for i,v in enumerate(values):
            if v is None:
                continue
            px=positions[i]
            # Reserve a dedicated annotation strip above each trend.
            # The 10-point standard history fits one label lane in the
            # compact rows; dense histories retain two staggered lanes.
            dense=len(history)>10
            plot_bottom=bottom+4 if row_index==0 else bottom+3
            plot_top=top-(22 if row_index==0 else (18 if dense else 12))
            py=plot_bottom+max(1,plot_top-plot_bottom)*(v-low)/span
            points.append((px,py))
            # Numeric annotations for every result, staggered in two lanes.
            val=value(v,decimals)
            fs=6.2 if len(history)>10 else 6.8
            vx=date_positions[i][1]
            lane=i%2 if row_index==0 or len(history)>10 else 0
            label_y=top-8-lane*8
            text(vx-pdfmetrics.stringWidth(val,"Helvetica",fs)/2,label_y,val,fs,
                 i==len(values)-1,RED if i==len(values)-1 else INK)
        for p,q in zip(points,points[1:]):
            line(*p,*q,RED,1)
        for j,(px,py) in enumerate(points):
            c.setFillColor(RED)
            c.circle(px,py,2.6 if j==len(points)-1 else 1.5,stroke=0,fill=1)
        line(MARGIN,bottom,W-MARGIN,bottom,PALE,.7)
        y=bottom
    # Optional footer messages are controlled entirely by report_config.
    if is_synthetic and config.get("show_generated_footer_notice", True):
        text(MARGIN,54,"Synthetic demo fields present; not device-measured.",6.8,True,RED)
    line(MARGIN,43,W-MARGIN,43,RED,1)
    if config["show_generated_footer_notice"]:
        text(MARGIN,30,("SYNTHETIC DEMO - NOT REAL SCAN RESULTS" if is_synthetic else "GENERATED REPORT - NOT AN ORIGINAL INBODY RESULT SHEET"),7,True,RED)
    if config.get("show_tracking_footer",True):
        text(MARGIN,19,("Fictional software demonstration - not for medical use." if is_synthetic else "For personal tracking; not a diagnostic or device-verified measurement."),6.8,color=GRAY)
    c.save()
    return out.getvalue()
