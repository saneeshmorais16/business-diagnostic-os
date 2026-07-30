import re
from pathlib import Path
import pandas as pd
REQUIRED={"financial":["date","revenue","gross_profit","operating_cost","budget_revenue"],"operations":["date","cycle_time_hours","throughput","error_rate","on_time_rate","backlog"],"sales":["date","leads","opportunities","wins","sales_value","acquisition_cost"],"customer_service":["date","contacts","complaints","response_time_hours","resolution_time_hours","satisfaction_score","first_contact_resolution","sla_compliance"],"employee":["date","headcount","leavers","absent_days","available_days","vacancies","training_completion","revenue_per_employee"]}
def safe_filename(name): return (re.sub(r"[^A-Za-z0-9._-]","_",Path(name).name)[:120] or "upload.csv")
def validate_dataframe(df,kind):
    if kind not in REQUIRED:return [{"severity":"error","type":"dataset_type","message":"Unsupported dataset type"}]
    issues=[]; missing=[c for c in REQUIRED[kind] if c not in df.columns]
    issues += [{"severity":"error","type":"required_column","column":c,"message":f"Required column '{c}' is missing"} for c in missing]
    if missing:return issues
    if df.empty:return [{"severity":"error","type":"empty","message":"Dataset has no rows"}]
    for c in REQUIRED[kind]:
        if df[c].isna().any():issues.append({"severity":"error","type":"missing_value","column":c,"message":f"{df[c].isna().sum()} missing value(s)"})
    if df.duplicated().any():issues.append({"severity":"error","type":"duplicate","message":f"{df.duplicated().sum()} duplicate row(s)"})
    dates=pd.to_datetime(df.date,errors="coerce")
    if dates.isna().any():issues.append({"severity":"error","type":"date","column":"date","message":"One or more dates are invalid"})
    if dates.duplicated().any():issues.append({"severity":"warning","type":"date","column":"date","message":"Duplicate reporting periods detected"})
    for c in REQUIRED[kind][1:]:
        n=pd.to_numeric(df[c],errors="coerce")
        if n.isna().sum()>df[c].isna().sum():issues.append({"severity":"error","type":"data_type","column":c,"message":"Non-numeric value detected"});continue
        if (n<0).any():issues.append({"severity":"error","type":"impossible_value","column":c,"message":"Negative value is not permitted"})
        if len(n)>=4 and n.std()>0 and (((n-n.mean()).abs()/n.std())>3).any():issues.append({"severity":"warning","type":"outlier","column":c,"message":"Extreme outlier requires review"})
        if ("rate" in c or "completion" in c) and (n>100).any():issues.append({"severity":"error","type":"impossible_value","column":c,"message":"Percentage cannot exceed 100"})
    return issues
def calculate_kpis(df,kind):
    a,b=df.iloc[0],df.iloc[-1]; pct=lambda x,y:round((y/x-1)*100,1) if x else 0
    if kind=="financial":return {"Revenue growth":pct(a.revenue,b.revenue),"Gross margin":round(b.gross_profit/b.revenue*100,1),"Operating margin":round((b.revenue-b.operating_cost)/b.revenue*100,1),"Cost growth":pct(a.operating_cost,b.operating_cost),"Cost-to-income":round(b.operating_cost/b.revenue*100,1),"Budget variance":round((b.revenue-b.budget_revenue)/b.budget_revenue*100,1)}
    if kind=="operations":return {"Cycle time":float(b.cycle_time_hours),"Throughput":float(b.throughput),"Error rate":float(b.error_rate),"On-time completion":float(b.on_time_rate),"Backlog":float(b.backlog),"Average delay":round(float(df.cycle_time_hours.mean()),1)}
    if kind=="sales":return {"Conversion rate":round(b.wins/b.leads*100,1),"Average deal value":round(b.sales_value/b.wins,1),"Sales growth":pct(a.sales_value,b.sales_value),"Pipeline value":round(b.opportunities*(b.sales_value/b.wins),1),"Win rate":round(b.wins/b.opportunities*100,1),"Customer acquisition cost":round(b.acquisition_cost/b.wins,1)}
    if kind=="customer_service":return {"Response time":float(b.response_time_hours),"Resolution time":float(b.resolution_time_hours),"Complaint rate":round(b.complaints/b.contacts*100,1),"Satisfaction score":float(b.satisfaction_score),"First-contact resolution":float(b.first_contact_resolution),"Service-level compliance":float(b.sla_compliance)}
    return {"Employee turnover":round(b.leavers/b.headcount*100,1),"Absenteeism":round(b.absent_days/b.available_days*100,1),"Vacancy rate":round(b.vacancies/(b.headcount+b.vacancies)*100,1),"Training completion":float(b.training_completion),"Employee productivity":float(b.revenue_per_employee)}
def roi(initial,recurring,annual):
    net=annual-recurring; monthly=net/12
    return {"net_benefit":round(net,2),"roi_percentage":round(net/initial*100,1) if initial else None,"payback_months":round(initial/monthly,1) if monthly>0 else None}
def score_opportunity(s,w=None):
    w=w or {"impact":.25,"alignment":.15,"feasibility":.15,"time_to_value":.10,"readiness":.10,"risk":.15,"cost":.10}; score=sum(s[k]*w[k] for k in ["impact","alignment","feasibility","time_to_value","readiness"])+(6-s["risk"])*w["risk"]+(6-s["cost"])*w["cost"]; score=round(score/sum(w.values())*20,1)
    label="Quick Win" if score>=75 and s["difficulty"]<=2 else "Strategic Priority" if score>=75 else "Major Transformation" if s["impact"]>=4 and s["difficulty"]>=4 else "Do Not Pursue" if score<40 else "Defer"
    return score,label
def classify_stakeholder(i,n):return "Manage Closely" if i>=4 and n>=4 else "Keep Satisfied" if i>=4 else "Keep Informed" if n>=4 else "Monitor"
def diagnose(kpis,maturity=3):
    out=[]
    for metric,threshold,title,function,severity,high_bad in [("Operating margin",8,"Margin compression","Finance",5,False),("On-time completion",85,"Delivery reliability below target","Operations",5,False),("Complaint rate",5,"Complaint rate above tolerance","Customer service",4,True)]:
        if metric in kpis and ((high_bad and kpis[metric]>threshold) or (not high_bad and kpis[metric]<threshold)):out.append({"title":title,"function":function,"affected_kpi":metric,"severity":severity,"confidence":85,"finding_type":"confirmed finding"})
    if maturity<=2:out.append({"title":"Material capability gap","function":"Cross-functional","affected_kpi":"Maturity","severity":4,"confidence":65,"finding_type":"likely finding"})
    return out
