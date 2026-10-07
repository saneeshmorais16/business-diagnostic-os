# Security

Controls include strict Pydantic validation, parameterised ORM queries, structured errors, security response headers, filename basename extraction and character allow-listing, CSV-only extension and MIME checks, a configurable 5 MB limit, non-retention of invalid uploads, environment variables and audit events.

Runtime databases, environment files, uploads, caches and virtual environments are ignored. No secrets are committed. CSV formula injection is prevented at the trust boundary for future exports by prefixing values beginning with `=`, `+`, `-` or `@`; the current product does not re-export uploaded cells.

This portfolio MVP does not include authentication, authorisation, malware scanning, encryption key management or tenant isolation. Those are mandatory before processing real organisational data.
