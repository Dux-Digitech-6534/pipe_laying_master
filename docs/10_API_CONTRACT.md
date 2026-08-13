# API Contract

Namespace: `cmr_pipe_laying_master.api`

Phase 1 provides `bootstrap.get_bootstrap` for authenticated application identity. Planned API modules are dashboard, masters, material, pipe_laying, valve, restoration, and reports.

Rules:

- Read operations never mutate.
- Write operations check Frappe permissions server-side.
- Inputs are normalized and validated in services.
- Stock-affecting methods use standard ERPNext documents and transactions.
- Submit/cancel operations are idempotent and must not create duplicate downstream records.
- Item selection uses server-side search rather than downloading the entire Item master.
