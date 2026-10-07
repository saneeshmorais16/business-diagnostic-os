# Data dictionary

| Entity | Purpose | Important fields |
|---|---|---|
| Engagement | Consulting case | company, industry, revenue, objectives, status |
| CompanyProfile | Operating context | business model, locations, channels |
| FunctionalAssessment | Function health | maturity, importance, performance, evidence |
| DatasetUpload | Evidence ingestion | type, filename, row count, validation status |
| DataQualityIssue | Explicit validation result | severity, type, column, row, message |
| KPI | Trend observation | function, name, period, value, target, source |
| Finding | Supported business problem | evidence, severity, urgency, confidence, impact |
| Hypothesis / RootCause | Causal analysis | evidence for/against, confidence, validation action |
| Opportunity / BenefitEstimate | Investment option | cost, benefit range, readiness, risk, score |
| Recommendation | Executive proposal | eight-part consulting narrative |
| RoadmapInitiative | Delivery unit | owner, months, milestone, dependency, gate, KPI |
| Risk | Delivery threat | likelihood, impact, mitigation, contingency, owner |
| Stakeholder | Change actor | influence, interest, support, concern, approach |
| AuditEvent | Accountability | action, resource, timestamp, detail |

Currency is pounds sterling. Scores are ordinal 1–5 unless noted. Confidence is 0–100%. Money values are stored as numeric pounds; production financial systems should use fixed-precision decimals.
