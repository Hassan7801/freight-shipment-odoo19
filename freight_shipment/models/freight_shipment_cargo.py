from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FreightShipmentCargo(models.Model):

    _name = "freight.shipment.cargo"
    _description = "Shipment Cargo Item"
    _order = "id"

    shipment_id = fields.Many2one(
        "freight.shipment",
        string="Shipment",
        required=True,
        ondelete="cascade",
        index=True,
    )
    name = fields.Char(string="Description", required=True)
    quantity = fields.Float(required=True, default=1.0, digits=(16, 2))
    weight = fields.Float(string="Weight (kg)", required=True, digits=(16, 2))
    volume = fields.Float(string="Volume (m3)", required=True, digits=(16, 3))
    sequence = fields.Integer(default=10)

    @api.constrains("quantity", "weight", "volume")
    def _check_positive_values(self):
        for cargo in self:
            if cargo.quantity <= 0:
                raise ValidationError(_("Cargo quantity must be greater than zero."))
            if cargo.weight < 0:
                raise ValidationError(_("Cargo weight cannot be negative."))
            if cargo.volume < 0:
                raise ValidationError(_("Cargo volume cannot be negative."))
