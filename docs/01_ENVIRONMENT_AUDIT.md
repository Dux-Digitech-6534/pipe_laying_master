# CMR Pipe Laying Master — Environment Audit

Audit date: 12 August 2026  
Target site: `raisonigroup.duxdigitech.in`  
Bench: `/home/frappe/frappe-bench`  
Audit mode: read-only

## Confirmed application identity

| Item | Approved value |
|---|---|
| Python/Frappe app | `cmr_pipe_laying_master` |
| Module and title | `CMR Pipe Laying Master` |
| Desk route | `/app/cmr-pipe-laying-master` |
| Target site | `raisonigroup.duxdigitech.in` only |

No existing app directory, Module Def, DocType, Workspace, or Page collides with these names.

## Framework and toolchain

| Component | Version |
|---|---|
| Frappe | 16.12.0, `version-16` |
| ERPNext | 16.10.0, `version-16` |
| Python | 3.12.3 |
| Node.js | 24.14.0 |
| Yarn | 1.22.22 |

## Bench sites

- `erp.jewonline.in`
- `erptest.duxdigitech.in`
- `jewipl.duxdigitech.in`
- `raisonigroup.duxdigitech.in`
- `sanskruti.duxdigitech.in`
- `uwmerp.duxdigitech.in`

Only `raisonigroup.duxdigitech.in` is in scope for installation and migration.

## Apps installed on target site

- frappe
- erpnext
- material_indent
- gh_raisoni_reports
- dux_voucher
- dux_portal
- customize_purchase_receipt
- rgi_migration
- dux_groupview
- payment_indent
- dux_civil_works
- bank_clearance_custom
- fixed_asset_control
- purchase_register
- dux_digital_signature

The legacy `pipe_laying_inhouse` app exists on the shared bench but is **not installed** on `raisonigroup.duxdigitech.in`.

## Target-site data baseline

| Master | Current records |
|---|---:|
| Company | 6 |
| Project | 0 |
| Supplier | 3 |
| Warehouse | 30 |
| Item | 31 |
| Item Group | 7 |

Companies currently include Dux Digitech, four GH Raisoni institutions, and Sanskruti Developer. Every company currently has the standard group warehouse plus Stores, Work In Progress, Finished Goods, and Goods In Transit warehouses. No project records exist yet.

Current Item Groups are Products, Raw Material, Services, Sub Assemblies, Consumable, and Work Order Items under All Item Groups. Therefore pipe/fitting/valve/restoration groups must be configured or created deliberately; they must not be hard-coded.

Current Stock Entry Types are ERPNext defaults. No CMR/DUX contractor issue, return, pipe consumption, or valve consumption types exist.

## Existing custom metadata

No custom DocTypes exist on the target site. No custom roles are marked as custom. No Workspace exists with DUX, CMR, or Pipe names.

Relevant existing Custom Fields:

- Purchase Receipt: `custom_purchase_invoice_id`
- Stock Entry: `custom_username`, `custom_material_indent`, `custom_remark`, `custom_attachment`
- Stock Entry Detail: `custom_issue_qty`, `custom_material_indent`, `custom_material_indent_item`, `custom_specification`

No field beginning with `custom_cmr_` exists. New standard-DocType extensions must use `custom_cmr_...` names.

## Existing Purchase Receipt behaviour

Purchase Receipt is already affected by:

- `customize_purchase_receipt`: custom Desk JavaScript.
- `dux_voucher`: posting/backdating validation.
- `fixed_asset_control`: on-submit/on-cancel asset-bin synchronization.
- `purchase_register`: permission filtering plus before-save, validate, workflow, and update-after-submit hooks.
- Several enabled target-site Client Scripts for PO quantity, PO selection, activity, field hiding, and invoice attachment.

CMR Material Inward must create and operate on a standard Purchase Receipt, allowing all these validations/hooks to run. It must not override the Purchase Receipt controller or bypass permission checks.

## Existing Stock Entry behaviour

Stock Entry is already affected by:

- `material_indent`: validate and on-submit handlers.
- Enabled Client Scripts for default warehouse, material-indent display, warehouse fetch, default Stock Entry Type, and username/department splitting.
- An enabled Server Script named `Stock Entry`.

CMR material movement/consumption services must create standard Stock Entry documents and preserve their validation lifecycle. CMR references must be isolated and namespaced.

## Naming/property observations

- Item is configured as field-named by `item_code`; its naming-series UI is hidden.
- Supplier uses the standard Supplier master with a hidden configured series.
- Purchase Receipt and Stock Entry have site-specific naming-series/property setters.
- Proposed CMR transaction IDs must use their own DocType naming series and Frappe naming APIs.

## Phase 0 conclusion

The new app can be safely isolated under `apps/cmr_pipe_laying_master/` and installed only on `raisonigroup.duxdigitech.in`. The greatest integration risk is not a name collision; it is the existing Purchase Receipt/Stock Entry customization stack. CMR must wrap standard documents through services without replacing their standard or installed-app lifecycle.
