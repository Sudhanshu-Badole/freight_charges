import frappe
from frappe.tests import IntegrationTestCase


class IntegrationTestFreightSettings(IntegrationTestCase):
	def test_stock_item_rejected(self):
		item = frappe.get_all("Item", filters={"is_stock_item": 1}, pluck="name", limit=1)
		if not item:
			return
		doc = frappe.get_doc(
			{
				"doctype": "Freight Settings",
				"purchase_freight_item": item[0],
				"sales_freight_item": item[0],
				"freight_hsn_mode": "Inherit HSN",
			}
		)
		self.assertRaises(frappe.ValidationError, doc.validate)
