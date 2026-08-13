# Application Architecture

## Runtime

- Frappe/ERPNext authenticated Desk Page at `/app/cmr-pipe-laying-master`.
- Vue 3 component application compiled by Vite into the app's public assets.
- Namespaced whitelisted APIs under `cmr_pipe_laying_master.api`.
- Business rules in service modules, not Vue or API controllers.
- ERPNext Purchase Receipt and Stock Entry remain the inventory source of truth.

## Layering

```text
Vue pages/components
        ↓
CMR whitelisted APIs
        ↓
CMR services and validation
        ↓
CMR DocTypes + ERPNext standard documents
        ↓
ERPNext Stock Ledger
```

Version 1 is online-only. It contains no service worker, offline cache, outbox, replay engine, or external authentication.

## Frontend boundary

The Vue application provides the custom workflow and visual design. It does not become a second data store. Link searches, permissions, validations, calculations, save, submit, cancel, and stock checks are server operations.
