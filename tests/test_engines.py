import pandas as pd
import pytest
from app.engines import *
def frame(kind):
    rows={"financial":[["2025-01-01",100,40,92,110],["2025-02-01",110,44,99,115]],"operations":[["2025-01-01",10,100,2,90,5],["2025-02-01",14,110,3,80,8]],"sales":[["2025-01-01",100,40,20,2000,200],["2025-02-01",120,50,25,3000,250]],"customer_service":[["2025-01-01",100,4,2,10,4.2,80,90],["2025-02-01",100,6,3,12,3.8,75,85]],"employee":[["2025-01-01",100,2,20,2000,5,90,1000],["2025-02-01",100,3,30,2000,10,80,1100]]}
    return pd.DataFrame(rows[kind],columns=REQUIRED[kind])
@pytest.mark.parametrize("kind",list(REQUIRED))
def test_valid_dataset(kind):assert validate_dataframe(frame(kind),kind)==[]
@pytest.mark.parametrize("kind",list(REQUIRED))
def test_required_column(kind):assert validate_dataframe(frame(kind).drop(columns=[REQUIRED[kind][1]]),kind)[0]["type"]=="required_column"
@pytest.mark.parametrize("kind",list(REQUIRED))
def test_kpis_generated(kind):assert len(calculate_kpis(frame(kind),kind))>=5
@pytest.mark.parametrize("bad",["../evil.csv","..\\evil.csv","a b.csv","x<script>.csv"])
def test_filename_security(bad):assert "/" not in safe_filename(bad) and "\\" not in safe_filename(bad) and "<" not in safe_filename(bad)
def test_duplicate_rows():
    d=frame("financial");d=pd.concat([d,d.iloc[[0]]]);assert any(x["type"]=="duplicate" for x in validate_dataframe(d,"financial"))
def test_invalid_date():
    d=frame("financial");d.loc[0,"date"]="bad";assert any(x["type"]=="date" for x in validate_dataframe(d,"financial"))
def test_negative_value():
    d=frame("operations");d.loc[0,"throughput"]=-1;assert any(x["type"]=="impossible_value" for x in validate_dataframe(d,"operations"))
def test_missing_value():
    d=frame("sales");d.loc[0,"wins"]=None;assert any(x["type"]=="missing_value" for x in validate_dataframe(d,"sales"))
def test_unsupported_kind():assert validate_dataframe(pd.DataFrame(),"other")[0]["type"]=="dataset_type"
@pytest.mark.parametrize("initial,recurring,annual,net",[(100,10,110,100),(200,0,100,100),(50,60,40,-20)])
def test_roi_net(initial,recurring,annual,net):assert roi(initial,recurring,annual)["net_benefit"]==net
def test_roi_percentage():assert roi(100,20,120)["roi_percentage"]==100
def test_payback():assert roi(120,0,120)["payback_months"]==12
def test_zero_initial_cost():assert roi(0,0,120)["roi_percentage"] is None
@pytest.mark.parametrize("i,n,label",[(5,5,"Manage Closely"),(5,2,"Keep Satisfied"),(2,5,"Keep Informed"),(2,2,"Monitor")])
def test_stakeholder_classification(i,n,label):assert classify_stakeholder(i,n)==label
def test_quick_win():assert score_opportunity(dict(impact=5,alignment=5,feasibility=5,time_to_value=5,readiness=5,risk=1,cost=1,difficulty=1))[1]=="Quick Win"
def test_major_transformation():assert score_opportunity(dict(impact=5,alignment=2,feasibility=2,time_to_value=2,readiness=2,risk=4,cost=4,difficulty=5))[1]=="Major Transformation"
def test_low_score():assert score_opportunity(dict(impact=1,alignment=1,feasibility=1,time_to_value=1,readiness=1,risk=5,cost=5,difficulty=3))[1]=="Do Not Pursue"
def test_diagnose_margin():assert diagnose({"Operating margin":6})[0]["title"]=="Margin compression"
def test_diagnose_delivery():assert diagnose({"On-time completion":73})[0]["finding_type"]=="confirmed finding"
def test_diagnose_complaints():assert diagnose({"Complaint rate":7})[0]["severity"]==4
def test_diagnose_maturity():assert diagnose({},2)[0]["finding_type"]=="likely finding"
