{
    "name": "Freight Shipment Management",
    "version": "19.0.1.0.4",
    "category": "Inventory/Delivery",
    "summary": "Register shipment requests, manage delivery lifecycle, and print shipment orders",
    "description": """
Freight Shipment Management
Manage freight shipment requests end to end:

* Configure shipment types (Road, Air, Ocean, Parcel, ...)
* Register shipment requests with origin, destination, and dates
* Track multiple cargo items with automatic weight and volume totals
* Advance shipments through Preparing -> With Courier -> On the Way -> Delivered
* Print a shipment order PDF for the driver
    """,
    "author": "Hassan Ahmed",
    "license": "LGPL-3",
    "depends": ["mail", "contacts"],
    "data": [
        "security/freight_shipment_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/freight_shipment_type_data.xml",
        "report/freight_shipment_report.xml",
        "report/freight_shipment_templates.xml",
        "views/freight_shipment_type_views.xml",
        "views/freight_shipment_views.xml",
        "views/freight_shipment_menus.xml",
    ],
    "demo": [
        "data/freight_shipment_demo.xml",
    ],
    "installable": True,
    "application": True,
}
