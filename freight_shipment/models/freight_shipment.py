from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class FreightShipment(models.Model):

    _name = "freight.shipment"
    _description = "Freight Shipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"
    _rec_name = "name"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
        tracking=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        index=True,
    )
    shipment_type_id = fields.Many2one(
        "freight.shipment.type",
        string="Shipment Type",
        required=True,
        tracking=True,
        index=True,
    )
    shipment_type_category = fields.Selection(
        related="shipment_type_id.category",
        string="Type Category",
        store=True,
    )
    origin = fields.Char(required=True, tracking=True)
    destination = fields.Char(required=True, tracking=True)
    date_pickup = fields.Date(string="Requested Pickup Date", required=True, tracking=True)
    date_delivery = fields.Date(string="Requested Delivery Date", required=True, tracking=True)
    state = fields.Selection(
        selection=[
            ("preparing", "Preparing"),
            ("with_courier", "With Courier"),
            ("on_the_way", "On the Way"),
            ("delivered", "Delivered"),
        ],
        string="Status",
        default="preparing",
        required=True,
        copy=False,
        tracking=True,
        group_expand=True,
        index=True,
    )
    cargo_ids = fields.One2many(
        "freight.shipment.cargo",
        "shipment_id",
        string="Cargo Items",
        copy=True,
    )
    cargo_count = fields.Integer(compute="_compute_totals", store=True)
    total_weight = fields.Float(
        string="Total Weight (kg)",
        compute="_compute_totals",
        store=True,
        digits=(16, 2),
    )
    total_volume = fields.Float(
        string="Total Volume (m3)",
        compute="_compute_totals",
        store=True,
        digits=(16, 3),
    )
    notes = fields.Text()
    user_id = fields.Many2one(
        "res.users",
        string="Responsible",
        default=lambda self: self.env.user,
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        index=True,
    )

    @api.depends(
        "cargo_ids.quantity",
        "cargo_ids.weight",
        "cargo_ids.volume",
    )
    def _compute_totals(self):
        for shipment in self:
            cargo = shipment.cargo_ids
            shipment.cargo_count = len(cargo)
            shipment.total_weight = sum(cargo.mapped("weight"))
            shipment.total_volume = sum(cargo.mapped("volume"))

    @api.constrains("date_pickup", "date_delivery")
    def _check_dates(self):
        for shipment in self:
            if (
                shipment.date_pickup
                and shipment.date_delivery
                and shipment.date_delivery < shipment.date_pickup
            ):
                raise ValidationError(
                    _("The requested delivery date cannot be earlier than the pickup date.")
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) in (False, _("New")):
                vals["name"] = self.env["ir.sequence"].next_by_code("freight.shipment") or _("New")
        return super().create(vals_list)

    def write(self, vals):
        if "state" in vals and not self.env.context.get("shipment_state_change"):
            raise UserError(
                _(
                    "You cannot change the shipment status directly. "
                    "Use the action buttons to move it through the delivery lifecycle."
                )
            )
        return super().write(vals)

    def _set_state(self, new_state):
        labels = dict(self._fields["state"].selection)
        for shipment in self:
            old_label = labels.get(shipment.state, shipment.state)
            new_label = labels.get(new_state, new_state)
            shipment._track_set_log_message(
                _("Status moved from %(old)s to %(new)s.")
                % {"old": old_label, "new": new_label}
            )
            shipment.with_context(shipment_state_change=True).write({"state": new_state})

    def action_send_to_courier(self):
        for shipment in self:
            if shipment.state != "preparing":
                raise UserError(_("Only shipments in Preparing can be handed to a courier."))
            if not shipment.cargo_ids:
                raise UserError(
                    _(
                        "Shipment %(reference)s has no cargo items yet. "
                        "Add at least one cargo item before handing it to the courier."
                    )
                    % {"reference": shipment.name}
                )
            shipment._set_state("with_courier")

    def action_start_delivery(self):
        for shipment in self:
            if shipment.state != "with_courier":
                raise UserError(_("Only shipments with a courier can start delivery."))
            shipment._set_state("on_the_way")

    def action_mark_delivered(self):
        for shipment in self:
            if shipment.state != "on_the_way":
                raise UserError(_("Only shipments that are on the way can be marked as delivered."))
            shipment._set_state("delivered")

    def action_reset_to_preparing(self):
        for shipment in self:
            if shipment.state == "delivered":
                raise UserError(_("Delivered shipments cannot be reset."))
            shipment._set_state("preparing")
