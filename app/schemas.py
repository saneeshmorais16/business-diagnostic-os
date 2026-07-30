from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
Industry=Literal["banking","retail","hospitality","healthcare","professional services","logistics","technology","manufacturing"]
class EngagementCreate(BaseModel):
    company_name:str=Field(min_length=2,max_length=180); industry:Industry; country:str="United Kingdom"; employees:int=Field(gt=0,le=10_000_000); annual_revenue:float=Field(gt=0); operating_cost:float=Field(ge=0)
    strategic_objectives:str=""; current_challenges:str=""; diagnostic_period:str="Last 12 months"; primary_stakeholder:str="Executive sponsor"; status:Literal["Draft","Active","Complete","On hold"]="Active"
class EngagementRead(EngagementCreate):
    id:int; model_config=ConfigDict(from_attributes=True)
class AssessmentCreate(BaseModel):
    function:str; maturity:int=Field(ge=1,le=5); importance:int=Field(ge=1,le=5); performance_score:int=Field(ge=1,le=5); evidence:str=""; pain_points:str=""; kpis:str=""; manual_processes:str=""; systems_used:str=""; data_quality:int=Field(default=3,ge=1,le=5); employee_feedback:str=""; customer_impact:str=""
