# Power App to ERPNext Mapping

| Power App structure | ERPNext / CMR owner | Decision |
|---|---|---|
| User Details and User Type | User, Role, User Permission | Reuse standard security |
| Site, Zone, Village, Store | CMR Site + Project + Warehouse | CMR Site owns location mapping; stock location stays Warehouse |
| Material Details | Item, Item Group, Item Attribute, UOM | Reuse standard masters |
| Supplier Details | Supplier | Reuse standard master |
| Contractor Details | Supplier + CMR Contractor Assignment | Supplier is party; assignment controls site/work/warehouse |
| New Material Inward | Purchase Receipt | Reuse standard buying and stock lifecycle |
| Inward Quantity Breakout | CMR Material Quantity Breakup child on Purchase Receipt | New child table |
| Material Issue | Stock Entry: CMR Contractor Issue | Standard Material Transfer |
| Material Return | Stock Entry: CMR Contractor Return | Standard Material Transfer back |
| Stock custom list | Bin / Stock Ledger Entry | Do not migrate custom balance table |
| Pipe Laying Details | CMR Pipe Laying Measurement | New submittable transaction |
| Pipe Details of PLM | CMR Pipe Segment child | New child table |
| Dismantling / Excavation | CMR Excavation Detail child | New child table with calculated/actual volume |
| Refilling | CMR Refill Detail child | New child table with volume calculation |
| Pipe Laying Fitting Details | CMR Fitting Consumption child | New child table; stock consumed on submit |
| Pipe Laying Valves Details | CMR Valve Installation | New submittable transaction |
| Valves & Fittings Details | CMR Valve Fitting Item child | New child table; stock consumed on submit |
| Restoration fields on pipe row | CMR Road Restoration | New linked submittable transaction |
| Power App email success message | Frappe notification/email hook | Add after workflow recipients are confirmed |
| Pipe Laying Approval screen | Frappe Workflow | Draft -> Pending Approval -> Approved/Rejected |
