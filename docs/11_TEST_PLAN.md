# Test Plan

Mandatory suites cover masters, Purchase Receipt inward, contractor issue/return, calculations, measurement submission/cancellation, segment creation, valve/restoration, permissions, stock integration, idempotency, rollback, and legacy isolation.

Phase 1 acceptance checks:

1. App is installed only on `raisonigroup.duxdigitech.in`.
2. `/app/cmr-pipe-laying-master` Page record exists.
3. Vue production build succeeds.
4. Bootstrap API returns authenticated application identity.
5. Page bundle and CSS exist in assets.
6. No CMR file references or changes the legacy app.
7. Legacy repository baseline remains unchanged.
