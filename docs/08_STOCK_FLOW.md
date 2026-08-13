# Stock Flow

```text
Purchase Order
  → Material Inward UI
  → Purchase Receipt
  → Project Warehouse
  → Contractor Issue (Stock Entry: Material Transfer)
  → Contractor Warehouse
      ├─ Pipe/Valve execution consumption (Stock Entry: Material Issue)
      └─ Material Return (Stock Entry: Material Transfer back)
```

Transfer to contractor custody is not consumption. All warehouses are explicit links, standard negative-stock and valuation validations remain active, and no custom balance table is permitted.

Planned Stock Entry Types: CMR Contractor Issue, CMR Contractor Return, CMR Pipe Consumption, and CMR Valve Consumption. Their standard ERPNext purposes must remain Material Transfer, Material Transfer, Material Issue, and Material Issue respectively.
