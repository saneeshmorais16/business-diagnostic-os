# Business Diagnostic OS

Business Diagnostic OS is an evidence-led management-consulting platform for diagnosing organisational performance, validating root causes, sizing opportunities and producing an executive transformation roadmap.

## Business problem

Leadership teams often have fragmented KPI packs, inconsistent stakeholder views and loosely connected improvement ideas. This application creates a traceable chain from context and evidence to findings, root-cause hypotheses, investment options, recommendations, delivery gates and benefits tracking.

## Product screenshots

Run the application and capture the Executive dashboard, Prioritisation and Executive report pages. The interface is responsive and the report has dedicated print styling.

## Consulting methodology

`Context → Problem definition → Hypotheses → Evidence gathering → Analysis → Root-cause validation → Options → Recommendation → Implementation roadmap → Benefits tracking`

Findings are labelled as confirmed, likely or requiring validation. Root-cause records include counter-evidence and validation actions. Benefits are explicitly indicative estimates.

## Features

- Engagement setup for eight industries and 11 business functions
- CSV ingestion for finance, operations, sales, service and employee data
- Required-column, type, missing-value, duplicate, date, impossible-value and outlier checks
- KPI trend calculation and Chart.js views
- Rules-based diagnostic findings with evidence, impact and confidence
- Editable-ready Five Whys / people-process-technology-data root-cause records
- Opportunity, ROI and scenario business cases
- Weighted prioritisation and impact-versus-effort matrix
- Consulting-format recommendations and 12-month roadmap
- Risk register, stakeholder map, executive dashboard and printable report
- Complete fictional NorthStar Retail demonstration with linked synthetic evidence
- Audit events, upload controls, secure headers and structured API errors

## Architecture

FastAPI serves REST endpoints and Jinja2 pages. SQLAlchemy persists the domain model in SQLite. pandas validates uploads and calculates KPIs. A deterministic rules and scoring layer keeps conclusions explainable. Chart.js provides client-side charts.

```text
Browser → FastAPI routes → domain/scoring engines → SQLAlchemy → SQLite
          Jinja2 + Chart.js       pandas CSV validation
```

See [architecture](docs/architecture.md) and [data dictionary](docs/data-dictionary.md).

## Technology

Python 3.12, FastAPI, SQLAlchemy, Pydantic, pandas, NumPy, Jinja2, HTML, CSS, JavaScript, Chart.js, pytest, Docker and GitHub Actions.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`, select **Open NorthStar demonstration**, or use API docs at `/docs`.

Seed the demonstration without opening the browser with `python -m app.cli seed`.

## Docker

```bash
docker compose up --build
```

## Tests

```bash
pytest -q
```

The suite covers validation, KPI maths, diagnostic rules, ROI, scoring, stakeholder classification, database CRUD/cascade behaviour, security headers, uploads and API validation.

## API usage

```bash
curl -X POST http://localhost:8000/api/v1/engagements \
  -H "Content-Type: application/json" \
  -d '{"company_name":"Example Ltd","industry":"technology","employees":100,"annual_revenue":5000000,"operating_cost":4000000}'
curl "http://localhost:8000/api/v1/engagements?page=1&page_size=20&industry=technology&sort=created_at&order=desc"
```

OpenAPI documentation describes all endpoints and validation contracts.

## NorthStar sample engagement

NorthStar Retail Ltd is a fictional UK omnichannel retailer with £48m revenue, 620 employees, 34 stores and a central warehouse. Synthetic source records support a 40% delivery-delay increase, stock-outs above target, 96 weekly reporting hours, margin compression and complaint growth linked to delivery and availability. See the [case study](docs/sample-case-study.md).

## Data model

The schema includes Engagement, CompanyProfile, FunctionalAssessment, DatasetUpload, DataQualityIssue, KPI, Finding, Hypothesis, RootCause, Opportunity, Recommendation, RoadmapInitiative, Risk, Stakeholder, BenefitEstimate and AuditEvent. Foreign keys, indexes, timestamps and appropriate cascade rules are defined in `app/models.py`.

## Security controls

Pydantic validation, parameterised SQLAlchemy access, filename sanitisation, extension/MIME allow-listing, 5 MB upload limits, rejected-file non-retention, secure headers, environment configuration and ignored runtime data. Spreadsheet exports should prefix formula-leading values; this MVP does not export user CSV content. See [security](docs/security.md).

## Assumptions and limitations

- NorthStar data and people are fictional; estimates are illustrative and labelled.
- Authentication/RBAC, multi-tenancy, migrations and cloud object storage are outside this portfolio MVP.
- Report export uses browser Print / Save as PDF rather than server-side PDF generation.
- Diagnostic logic is deterministic and explainable; no external LLM is required.
- Opportunity benefits are gross and are not automatically adjusted for overlap, tax or optimism bias.

## Future improvements

Add authentication, Alembic migrations, evidence editing workflows, benefit overlap modelling, industry rule packs, accessibility audit automation, PDF generation and optional governed LLM assistance with citations.
