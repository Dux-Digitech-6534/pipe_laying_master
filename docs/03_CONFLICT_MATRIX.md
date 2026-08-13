# CMR Pipe Laying Master — Conflict Matrix

| Proposed CMR area | Existing environment | Risk | Resolution |
|---|---|---:|---|
| App package `cmr_pipe_laying_master` | No existing app/path | Low | Safe to create |
| Module `CMR Pipe Laying Master` | No Module Def collision | Low | Safe to create |
| Route `/app/cmr-pipe-laying-master` | No Page/route collision | Low | Safe to create |
| CMR DocType names | No CMR/Pipe custom DocTypes on target | Low | Prefix every owned DocType with CMR |
| Legacy Pipe Laying | Shared-bench app, not target-installed, dirty source tree | Critical | Never edit/install/reuse it; record checksum/status |
| Material Inward | Purchase Receipt has multiple hooks, scripts, property setters, permissions | High | Use standard Purchase Receipt lifecycle; no controller override or validation bypass |
| Material Issue/Return | Stock Entry has material-indent hooks and scripts | High | Use standard Stock Entry lifecycle; test interaction with existing hooks |
| Stock consumption | Legacy uses `custom_pour_card*` references | Critical | Use new `custom_cmr_*` references only |
| Contractor warehouse | Legacy derives name from Contractor + abbreviation | High | Store explicit Warehouse link in CMR Contractor Assignment |
| Item master | Existing Item records/groups and custom naming | Medium | Reuse Item; server-side search; configurable Item Groups |
| Supplier/Contractor | Existing Supplier master has records and property setters | Medium | Reuse Supplier; add only CMR Assignment DocType |
| Warehouse | Standard warehouses exist per company; no contractor warehouses yet | Medium | Explicit mapping; validate company and non-group warehouse |
| Project | No projects currently exist | Medium | Reuse Project; CMR setup cannot transact until project/site hierarchy exists |
| Roles | No CMR roles exist | Low | Create namespaced CMR roles with least privilege |
| Stock Entry Type | Only standard types exist | Low | Create CMR-named types mapped to standard purposes |
| Calculation rules | Legacy desk/mobile rules differ | Critical | Do not copy; document undecided formulas as BUSINESS DECISION REQUIRED; Python authoritative |
| Physical Pipe No vs segment ID | Legacy common `PIPE-###` batching | High | Separate physical number from Frappe-named CMR Pipe Segment |
| Submitted edits | Legacy may add rows after submit | High | CMR V1 locks submitted documents; correction via cancel/amend |
| Frontend framework | Legacy contains React/PWA | Medium | CMR uses Vue 3 mounted in Frappe Desk; no PWA in V1 |
| Prototype mock arrays | Supplied HTML uses local demo state | High | Use DocTypes/APIs only; never migrate mock rows as production data |
| Workspace/Page | Existing Dux Portal and other DUX pages | Medium | Independent CMR Page and route; do not alter Dux Portal |
| Dashboard/report totals | Prototype contains hard-coded demo counts | High | Server-side queries and ERPNext stock ledger only |

## Blocking business decisions

These do not block Phase 1 shell/scaffolding, but they block stock-affecting Pipe Laying submission:

1. Final calculation definitions for excavation, soil, hard rock, refilling, restoration, and balance quantities.
2. Authoritative duplicate-measurement business key.
3. Which target Company/Companies will use the application.
4. Approved Item Group structure for pipe, fitting, valve, and restoration materials.
5. Approved Project, Site, and Warehouse hierarchy.
6. Cancellation policy for created Pipe Segments: cancelled status versus document cancellation.

No arbitrary formula or duplicate key may be enforced until approved.
