# Deployment Plan

## Scope

Deploy to raisonigroup.duxdigitech.in and jewipl.duxdigitech.in on the shared production bench.

## Phase deployment procedure

1. Record target installed apps and legacy repository checksum/status.
2. Sync only `apps/cmr_pipe_laying_master/` source.
3. Install frontend dependencies when package metadata changes.
4. Build CMR frontend assets.
5. Run `bench --site <target-site> migrate` when schema/Page metadata changes.
6. Clear target-site cache.
7. Run CMR tests and route/API smoke checks.
8. Recheck target installed apps and legacy checksum/status.

No command may run `--site all`. Run site commands only for an explicitly approved target; never use --site all.
