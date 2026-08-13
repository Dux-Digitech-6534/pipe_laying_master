# CMR Pipe Laying Master — Legacy Safety Boundary

## Protected legacy application

| Property | Value |
|---|---|
| App | `pipe_laying_inhouse` |
| Bench path | `/home/frappe/frappe-bench/apps/pipe_laying_inhouse` |
| Git commit at audit | `7f72c35793b98b9726893a3938ba58e9603e207d` |
| Tree checksum at audit | `e2ece1389b835626bc5de47f21b90652473b11a15b02926b27d8dd8407fcab55` |
| Target-site status | Not installed on `raisonigroup.duxdigitech.in` |

The legacy repository already contains pre-existing modified and untracked files. They belong to the production legacy implementation and are not part of CMR work. They must neither be cleaned nor normalized.

## Absolute do-not-touch list

CMR development must not modify:

- Any file under `apps/pipe_laying_inhouse/`.
- Legacy DocTypes including Pour Card and its child tables.
- Legacy APIs, hooks, fixtures, PWA, service worker, or `/pipe-laying/` route.
- Legacy formulas, common Pipe ID logic, permissions, reports, or offline queue.
- Legacy Stock Entry fields `custom_pour_card` and `custom_pour_card_town`.
- Any JEWIPL site database or configuration.

## CMR isolation rules

- All CMR source lives under `apps/cmr_pipe_laying_master/`.
- All CMR-owned DocTypes start with `CMR`.
- All standard-DocType Custom Fields start with `custom_cmr_`.
- The CMR route is `/app/cmr-pipe-laying-master`.
- Version 1 is online, desktop-first, and has no PWA/service worker/offline queue.
- Contractor warehouse mapping is explicit in CMR Contractor Assignment; it is never derived from a name.
- CMR uses standard Purchase Receipt and Stock Entry ledgers without using legacy Pour Card references.

## Regression checks

Before and after every deploy phase:

1. Confirm the legacy repository commit and working-tree status were not changed by CMR work.
2. Confirm the legacy source-tree checksum remains identical unless independent user-owned legacy work occurs.
3. Confirm `/pipe-laying/` files/routes were not created or overwritten by CMR.
4. Confirm `custom_pour_card` and `custom_pour_card_town` were not created, changed, or reused on the target site.
5. Confirm CMR is installed only on the approved target site.

## Current boundary status

Phase 0 used read-only commands. No legacy file, DocType, site, field, database record, route, hook, or permission was modified.
