# Power App Migration Specification

Source: `CMR PIPE LAYING.docx`, reviewed on 2026-08-12. The reference contains 26 embedded application screenshots and 21 documented add-entry screens with Power Fx formulas.

## Roles and navigation

- User: Home, Material Inward, Material Issue, Material Return, Pipe Laying Measurement, Valve Details, Road Restoration, and view screens.
- Approver: all user menus plus Pipe Laying Approval.
- ERP implementation: CMR Site Engineer and CMR Store User create operational drafts; CMR Project Manager approves/submits; CMR Pipe Admin has full access; CMR Pipe Viewer is read-only.

## Material Inward

1. Select Site/Project and Store.
2. Capture PO, MRN/GRN, inward date, supplier, vehicle type/number, transporter, transport cost, driver, LR number, attachments, remarks, and four verifier identities.
3. Add invoice/material lines with Item Type, MOC, class/pressure rating, diameter, item, quantity, UOM, rate, GST, amount, invoice date/no/status, and consumable classification.
4. Optionally capture pipe/roll quantity breakout (nos x length = total length).
5. Save and optionally add another invoice/material line.

ERP owner: standard Purchase Receipt and Purchase Receipt Item, extended only with `custom_cmr_` fields and the CMR Material Quantity Breakup child table. Submission updates the standard Stock Ledger.

## Material Issue and Return

- Header: date, site/project, source store, destination store or contractor, receiver, and remarks.
- Lines: material type, MOC, class, diameter, item, current stock, receiver stock, quantity, rate, UOM, and amount.
- Validation: quantity cannot exceed the source warehouse balance.

ERP owner: standard Stock Entry. Contractor custody uses an explicit contractor warehouse, never a custom balance table.

## Pipe Laying Measurement

1. Work information: date, project/site, work type, zone, village, section incharge, contractor, and single/multiple laying mode.
2. One or more pipe segments: pipe no/item, nodes, chainage, diameter, MOC, class, contractor stock, drawing length, and actual laid length.
3. Dismantling/excavation: cement concrete pavement, ordinary soil, and hard rock; length, width, calculated/actual depth and quantity plus GPS endpoints.
4. Refilling: murum, excavated earth, metal, stone dust, sand, and good earth. Quantity = length x width x depth.
5. Fittings: item, contractor stock, quantity, junction no, material attributes, and GPS location.
6. Completion: restoration required, end cap, remarks, approval, and execution stock consumption.

ERP owner: CMR Pipe Laying Measurement with CMR Pipe Segment, CMR Excavation Detail, CMR Refill Detail, and CMR Fitting Consumption children. Submission creates a standard CMR Pipe Consumption Stock Entry.

## Valve Installation

1. Select a submitted pipe measurement/segment still pending valve completion.
2. Capture contractor, valve item, quantity, chamber size, specific location, and GPS.
3. Add valve fitting items with contractor stock validation.
4. Submit and mark the selected segment valve status Completed.

ERP owner: CMR Valve Installation with CMR Valve Fitting Item. Submission creates a standard CMR Valve Consumption Stock Entry.

## Road Restoration

1. Select a submitted pipe segment where restoration is required and pending.
2. Show inherited pipe/site/zone/village/node/chainage/specification details.
3. Capture contractor/date, restoration width/length, M15/M20/M30 lengths and depths, GPS endpoints, and remarks.
4. Calculate each concrete quantity as length x restoration width x depth.
5. Submit and mark the selected segment restoration status Completed.

ERP owner: CMR Road Restoration linked to the measurement and pipe no.

## Non-negotiable behavior

- No mock arrays or separate custom stock balance table.
- No negative-stock bypass.
- All stock movements use Purchase Receipt, Stock Entry, and Stock Ledger Entry.
- Server-side validation is authoritative; frontend visibility is not security.
- CMR-owned DocTypes use the CMR prefix; standard extensions use `custom_cmr_`.
- Draft, submit, cancel, and downstream stock references must remain traceable and idempotent.
