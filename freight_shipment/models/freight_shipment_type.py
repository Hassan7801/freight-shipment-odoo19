from odoo import fields, models


class FreightShipmentType(models.Model):

    _name = "freight.shipment.type"
    _description = "Shipment Type"
    _order = "name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    category = fields.Selection(
        selection=[
            ("road", "Road"),
            ("air", "Air"),
            ("ocean", "Ocean"),
            ("parcel", "Parcel"),
            ("other", "Other"),
        ],
        required=True,
        default="road",
    )
    active = fields.Boolean(default=True)
    description = fields.Text()
    shipment_count = fields.Integer(compute="_compute_shipment_count")

    _code_uniq = models.Constraint(
        "UNIQUE (code)",
        "Shipment type code must be unique.",
    )

    def _compute_shipment_count(self):
        grouped = self.env["freight.shipment"]._read_group(
            [("shipment_type_id", "in", self.ids)],
            ["shipment_type_id"],
            ["__count"],
        )
        counts = {shipment_type.id: count for shipment_type, count in grouped}
        for shipment_type in self:
            shipment_type.shipment_count = counts.get(shipment_type.id, 0)

    def action_open_shipments(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Shipments",
            "res_model": "freight.shipment",
            "view_mode": "list,kanban,form",
            "domain": [("shipment_type_id", "=", self.id)],
            "context": {"default_shipment_type_id": self.id},
        }
