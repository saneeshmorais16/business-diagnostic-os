import io, os, uuid
from contextlib import asynccontextmanager
from pathlib import Path
import pandas as pd
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import *
from .schemas import EngagementCreate, EngagementRead, AssessmentCreate
from .engines import REQUIRED, calculate_kpis, roi, safe_filename, validate_dataframe
from .seed import seed_demo

BASE=Path(__file__).resolve().parent; UPLOADS=Path(os.getenv("UPLOAD_DIR",BASE.parent/"uploads")); MAX_UPLOAD=int(os.getenv("MAX_UPLOAD_BYTES","5242880"))
@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine); UPLOADS.mkdir(exist_ok=True); yield
app=FastAPI(title="Business Diagnostic OS",version="1.0.0",description="Evidence-led business diagnostics and transformation planning",lifespan=lifespan)
app.mount("/static",StaticFiles(directory=BASE/"static"),name="static"); templates=Jinja2Templates(directory=BASE/"templates")
@app.middleware("http")
async def security(request,call_next):
    response=await call_next(request); response.headers.update({"X-Content-Type-Options":"nosniff","X-Frame-Options":"DENY","Referrer-Policy":"strict-origin-when-cross-origin","Content-Security-Policy":"default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; img-src 'self' data:;"});return response
@app.exception_handler(HTTPException)
async def http_error(request,exc):return JSONResponse(status_code=exc.status_code,content={"error":{"status":exc.status_code,"message":exc.detail,"path":request.url.path}})
def engagement_or_404(db,id):
    obj=db.get(Engagement,id)
    if not obj:raise HTTPException(404,"Engagement not found")
    return obj
def ctx(db,e,page):
    return {"engagement":e,"page":page,"assessments":db.query(FunctionalAssessment).filter_by(engagement_id=e.id).all(),"findings":db.query(Finding).filter_by(engagement_id=e.id).order_by(Finding.severity.desc()).all(),"opportunities":db.query(Opportunity).filter_by(engagement_id=e.id).order_by(Opportunity.priority_score.desc()).all(),"kpis":db.query(KPI).filter_by(engagement_id=e.id).all(),"risks":db.query(Risk).filter_by(engagement_id=e.id).order_by(Risk.overall_rating.desc()).all(),"stakeholders":db.query(Stakeholder).filter_by(engagement_id=e.id).all(),"roadmap":db.query(RoadmapInitiative).filter_by(engagement_id=e.id).order_by(RoadmapInitiative.start_month).all(),"recommendations":db.query(Recommendation).join(Opportunity).filter(Opportunity.engagement_id==e.id).all(),"roots":db.query(RootCause).join(Finding).filter(Finding.engagement_id==e.id).all(),"uploads":db.query(DatasetUpload).filter_by(engagement_id=e.id).all()}
@app.get("/",response_class=HTMLResponse)
def home(request:Request,db:Session=Depends(get_db)):return templates.TemplateResponse(request,"landing.html",{"engagements":db.query(Engagement).count()})
@app.get("/engagements",response_class=HTMLResponse)
def engagements(request:Request,db:Session=Depends(get_db)):return templates.TemplateResponse(request,"engagements.html",{"engagements":db.query(Engagement).all()})
@app.get("/engagements/new",response_class=HTMLResponse)
def new(request:Request):return templates.TemplateResponse(request,"new.html",{})
@app.post("/engagements")
def create_form(company_name:str=Form(),industry:str=Form(),country:str=Form("United Kingdom"),employees:int=Form(),annual_revenue:float=Form(),operating_cost:float=Form(),strategic_objectives:str=Form(""),current_challenges:str=Form(""),primary_stakeholder:str=Form("Executive sponsor"),db:Session=Depends(get_db)):
    data=EngagementCreate(company_name=company_name,industry=industry,country=country,employees=employees,annual_revenue=annual_revenue,operating_cost=operating_cost,strategic_objectives=strategic_objectives,current_challenges=current_challenges,primary_stakeholder=primary_stakeholder);e=Engagement(**data.model_dump());db.add(e);db.flush();db.add(AuditEvent(engagement_id=e.id,action="created",resource_type="Engagement",resource_id=e.id));db.commit();return RedirectResponse(f"/engagements/{e.id}/overview",303)
@app.post("/demo")
def demo(db:Session=Depends(get_db)):e=seed_demo(db);return RedirectResponse(f"/engagements/{e.id}/dashboard",303)
@app.get("/engagements/{id}/{page}",response_class=HTMLResponse)
def workspace(id:int,page:str,request:Request,db:Session=Depends(get_db)):
    allowed={"overview","assessment","upload","data-quality","kpis","findings","root-causes","opportunities","prioritisation","recommendations","roadmap","risks","stakeholders","dashboard","report"}
    if page not in allowed:raise HTTPException(404,"Page not found")
    e=engagement_or_404(db,id);data=ctx(db,e,page);data["request"]=request
    return templates.TemplateResponse(request,"workspace.html",data)
@app.post("/engagements/{id}/upload")
async def upload(id:int,dataset_type:str=Form(),file:UploadFile=File(),db:Session=Depends(get_db)):
    engagement_or_404(db,id); name=safe_filename(file.filename or "upload.csv")
    if not name.lower().endswith(".csv") or file.content_type not in {"text/csv","application/vnd.ms-excel","application/csv"}:raise HTTPException(415,"Only CSV files are accepted")
    content=await file.read(MAX_UPLOAD+1)
    if len(content)>MAX_UPLOAD:raise HTTPException(413,"Upload exceeds 5 MB limit")
    try:df=pd.read_csv(io.BytesIO(content))
    except Exception:raise HTTPException(422,"CSV could not be parsed")
    issues=validate_dataframe(df,dataset_type);stored=f"{uuid.uuid4().hex}_{name}"; status="rejected" if any(x["severity"]=="error" for x in issues) else "validated"
    if status=="validated":(UPLOADS/stored).write_bytes(content)
    u=DatasetUpload(engagement_id=id,dataset_type=dataset_type,original_filename=name,stored_filename=stored if status=="validated" else "",row_count=len(df),status=status);db.add(u);db.flush()
    for x in issues:db.add(DataQualityIssue(upload_id=u.id,severity=x["severity"],issue_type=x["type"],column_name=x.get("column"),message=x["message"]))
    if status=="validated":
        for n,v in calculate_kpis(df,dataset_type).items():db.add(KPI(engagement_id=id,function=dataset_type.replace("_"," ").title(),name=n,period=str(df.iloc[-1].date),value=v,unit="metric",source=name))
    db.add(AuditEvent(engagement_id=id,action="uploaded",resource_type="DatasetUpload",resource_id=u.id,detail=f"{status}: {len(issues)} validation finding(s)"));db.commit();return RedirectResponse(f"/engagements/{id}/data-quality",303)
@app.get("/methodology",response_class=HTMLResponse)
def methodology(request:Request):return templates.TemplateResponse(request,"methodology.html",{})
@app.get("/about",response_class=HTMLResponse)
def about(request:Request):return templates.TemplateResponse(request,"about.html",{})
# REST API
@app.get("/api/v1/engagements",response_model=list[EngagementRead])
def list_api(db:Session=Depends(get_db),page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),industry:str|None=None,status:str|None=None,sort:str="created_at",order:str="desc"):
    q=db.query(Engagement)
    if industry:q=q.filter_by(industry=industry)
    if status:q=q.filter_by(status=status)
    col=getattr(Engagement,sort,None)
    if col is None:raise HTTPException(400,"Invalid sort field")
    return q.order_by(col.desc() if order=="desc" else col.asc()).offset((page-1)*page_size).limit(page_size).all()
@app.post("/api/v1/engagements",response_model=EngagementRead,status_code=201)
def create_api(data:EngagementCreate,db:Session=Depends(get_db)):e=Engagement(**data.model_dump());db.add(e);db.commit();db.refresh(e);return e
@app.get("/api/v1/engagements/{id}",response_model=EngagementRead)
def get_api(id:int,db:Session=Depends(get_db)):return engagement_or_404(db,id)
@app.delete("/api/v1/engagements/{id}",status_code=204)
def delete_api(id:int,db:Session=Depends(get_db)):db.delete(engagement_or_404(db,id));db.commit()
@app.get("/api/v1/engagements/{id}/findings")
def findings_api(id:int,db:Session=Depends(get_db),function:str|None=None):engagement_or_404(db,id);q=db.query(Finding).filter_by(engagement_id=id);return q.filter_by(function=function).all() if function else q.all()
@app.get("/api/v1/engagements/{id}/opportunities")
def opportunities_api(id:int,db:Session=Depends(get_db),classification:str|None=None):engagement_or_404(db,id);q=db.query(Opportunity).filter_by(engagement_id=id);return q.filter_by(classification=classification).all() if classification else q.all()
@app.get("/api/v1/opportunities/{id}/business-case")
def business_case(id:int,db:Session=Depends(get_db)):
    o=db.get(Opportunity,id)
    if not o:raise HTTPException(404,"Opportunity not found")
    return {**roi(o.initial_cost,o.recurring_cost,o.annual_benefit),"initial_cost":o.initial_cost,"recurring_cost":o.recurring_cost,"annual_benefit":o.annual_benefit,"label":"Indicative estimate; validate before investment decision"}
@app.get("/health")
def health():return {"status":"ok"}
