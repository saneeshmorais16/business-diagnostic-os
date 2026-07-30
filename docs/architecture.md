# Architecture

The application uses a deliberately small modular monolith. FastAPI handles HTML and REST delivery; Pydantic validates external input; SQLAlchemy models the consulting domain; SQLite provides portable persistence; pandas validates evidence and derives KPI values; Jinja2 and Chart.js render the decision experience.

## Boundaries

- `main.py`: HTTP, pagination, filtering, uploads, headers and views.
- `models.py`: persistent domain entities, indexes and lifecycle rules.
- `engines.py`: pure, testable validation, KPI, ROI, diagnostic and scoring logic.
- `seed.py`: fictional NorthStar evidence graph.
- `templates/` and `static/`: responsive UI and print report.

The rule engine returns confidence-labelled findings and does not call an opaque model. AuditEvent records important mutations. A production deployment should add Alembic, PostgreSQL, authenticated tenancy, object storage and background analysis jobs.
