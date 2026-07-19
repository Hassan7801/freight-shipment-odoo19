# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests import tagged, TransactionCase


@tagged("post_install", "-at_install")
class TestFreightShipment(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Customer"})
        cls.shipment_type = cls.env["freight.shipment.type"].create({
            "name": "Test Road",
            "code": "TEST_ROAD",
            "category": "road",
        })

    def _create_shipment(self, with_cargo=True):
        shipment = self.env["freight.shipment"].create({
            "partner_id": self.partner.id,
            "shipment_type_id": self.shipment_type.id,
            "origin": "Warehouse A",
            "destination": "Customer B",
            "date_pickup": "2026-07-18",
            "date_delivery": "2026-07-20",
        })
        if with_cargo:
            self.env["freight.shipment.cargo"].create({
                "shipment_id": shipment.id,
                "name": "Test cargo",
                "quantity": 2,
                "weight": 12.5,
                "volume": 0.8,
            })
        return shipment

    def test_sequence_assigned(self):
        shipment = self._create_shipment()
        self.assertTrue(shipment.name.startswith("SHP/"))

    def test_totals_recompute(self):
        shipment = self._create_shipment()
        self.env["freight.shipment.cargo"].create({
            "shipment_id": shipment.id,
            "name": "Extra",
            "quantity": 1,
            "weight": 7.5,
            "volume": 0.2,
        })
        self.assertEqual(shipment.total_weight, 20.0)
        self.assertEqual(shipment.total_volume, 1.0)
        self.assertEqual(shipment.cargo_count, 2)

    def test_cannot_leave_preparing_without_cargo(self):
        shipment = self._create_shipment(with_cargo=False)
        with self.assertRaises(UserError):
            shipment.action_send_to_courier()

    def test_direct_state_write_blocked(self):
        shipment = self._create_shipment()
        with self.assertRaises(UserError):
            shipment.write({"state": "delivered"})

    def test_full_lifecycle(self):
        shipment = self._create_shipment()
        shipment.action_send_to_courier()
        self.assertEqual(shipment.state, "with_courier")
        shipment.action_start_delivery()
        self.assertEqual(shipment.state, "on_the_way")
        shipment.action_mark_delivered()
        self.assertEqual(shipment.state, "delivered")

    def test_delivery_before_pickup_rejected(self):
        with self.assertRaises(Exception):
            self.env["freight.shipment"].create({
                "partner_id": self.partner.id,
                "shipment_type_id": self.shipment_type.id,
                "origin": "A",
                "destination": "B",
                "date_pickup": "2026-07-20",
                "date_delivery": "2026-07-18",
            })
