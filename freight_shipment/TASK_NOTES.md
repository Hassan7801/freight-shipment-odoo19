# Task Notes — Freight Shipment Management (Odoo 19)

## Context

The goal was a focused Odoo 19 application for a logistics team to:

1. Maintain reusable shipment types
2. Register shipment requests with a unique reference
3. Attach multiple cargo items with automatic weight/volume totals
4. Move each shipment through a fixed delivery lifecycle via explicit actions
5. Print a driver-facing shipment order PDF

**Assumptions made**

- Weight is stored in kilograms and volume in cubic metres — common logistics defaults, easy to change later.
- Shipment type *category* is a fixed selection (Road / Air / Ocean / Parcel / Other) while *type* itself remains a configurable master data record. That keeps reporting simple without forcing every nuance into a free-text field.
- Status must never be edited like a normal field. Transitions go through buttons only; kanban drag-and-drop is disabled for the same reason.
- A Manager-only “Reset to Preparing” action is included as a practical recovery path for mistakes before delivery. Delivered records stay locked.
- Multi-company, pricing, portals, and carrier APIs were deliberately left out of scope as requested.

## What you did

| Requirement | Outcome |
|---|---|
| Configurable shipment types with name, code, category, archive | `freight.shipment.type` + Configuration menu (Manager) |
| Unique shipment reference | Sequence `SHP/00001` assigned on create |
| Customer, type, origin, destination, pickup/delivery dates | Required fields on `freight.shipment` |
| Multiple cargo items | `freight.shipment.cargo` One2many lines |
| Auto totals for weight & volume | Stored computed fields, recomputed on line changes |
| Lifecycle Preparing → With Courier → On the Way → Delivered | Header buttons; statusbar is display-only |
| Block leaving Preparing with no cargo | Clear `UserError` on “Hand to Courier” |
| Status history | `mail.thread` + `tracking=True` on state (and key fields) → Chatter |
| Roles: User / Manager | Privilege-based groups; types writable only by Manager; no open ACL for all users |
| List, kanban (empty stages visible), form, search | Full UI under the **Shipments** app menu |
| PDF shipment order | QWeb report bound to the shipment |

## Findings, caveats, and setup

### Notable design choices

- **Three models, not one.** Header / lines / configuration mirrors how Odoo handles documents (sale order, picking). Totals stay honest because they are derived from lines.
- **Odoo 19 security.** Groups use `res.groups.privilege` (the 19.x pattern) under a dedicated Freight Shipment category.
- **Empty kanban columns.** `group_expand=True` on the Selection field keeps Preparing / With Courier / On the Way / Delivered visible even with zero records.


Automated tests already cover sequence, totals, cargo gate, direct-state block, full lifecycle, and date validation (`tests/test_freight_shipment.py`).

### Install and try

1. Add the module path to your Odoo addons path, for example:

   ```text
   .../projects/noptechs/custom
   ```

2. Update the apps list and install **Freight Shipment Management** (`freight_shipment`) on a fresh Odoo 19 database.

3. Assign a user the group **Freight Shipment / User** (or **Manager** to also edit shipment types).

4. Walkthrough:

   - **Configuration → Shipment Types** (Manager): confirm Road / Air / Ocean / Parcel, or create one
   - **Operations → Shipments**: create a request, add cargo lines, watch totals update
   - Use **Hand to Courier** → **Start Delivery** → **Mark Delivered**
   - Open the chatter to see status history
   - Print **Shipment Order** from the Print / gear menu
   - Try handing a shipment to the courier with no cargo to see the friendly error

5. Demo data (if the database was created with demo): one preparing shipment for “ACME Logistics Client” with two cargo lines.


### `freight.shipment.type`

Master data for modes of transport. Separate from shipments so a team lead can add/archive types without changing code, and so historical shipments keep a stable Many2one even if a type is later archived.

Fields: name, unique code, category, active, optional description.

### `freight.shipment`

The operational document. Holds who/what/where/when, the status, and computed totals. Inherits `mail.thread` / `mail.activity.mixin` for chatter history and future activities.

Why not store cargo as JSON or free text? Because totals, constraints, reporting, and the PDF all work better with real relational lines.

### `freight.shipment.cargo`

Simple child lines: description, quantity, weight, volume. Cascade-delete with the parent so orphan lines cannot remain.

### Why this structure

- Matches the brief’s behaviours with the least accidental complexity
- Keeps configuration (types) permission-separated from operations (shipments)
- Leaves a clean extension path for pricing, tracking numbers, or carrier APIs later — without baking them into this assignment
