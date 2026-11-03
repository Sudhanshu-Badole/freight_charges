import frappe
from frappe.tests import UnitTestCase

from freight_charges.freight_charges.allocation import allocate, group_rows


def _row(value, tmpl, nature="Stock", hsn="4819", itc=0):
	return {"value": value, "item_tax_template": tmpl, "nature": nature, "gst_hsn_code": hsn, "is_ineligible_for_itc": itc}


class UnitTestAllocation(UnitTestCase):
	def test_t01_two_rates(self):
		g = group_rows([_row(6000, "GST 18"), _row(4000, "GST 5")])
		shares = allocate(g, 1000)
		self.assertEqual(sorted(shares.values()), [400, 600])

	def test_t02_single_group(self):
		g = group_rows([_row(100, "GST 18"), _row(300, "GST 18")])
		self.assertEqual(len(g), 1)
		self.assertEqual(list(allocate(g, 1000).values()), [1000])

	def test_t03_rounding_sums_exactly(self):
		g = group_rows([_row(100, "A"), _row(100, "B"), _row(100, "C")])
		shares = allocate(g, 1000)
		self.assertEqual(round(sum(shares.values()), 2), 1000)
		self.assertEqual(sorted(shares.values()), [333.33, 333.33, 333.34])

	def test_t14_hsn_split_only_when_inheriting(self):
		rows = [_row(100, "GST 18", hsn="4819"), _row(100, "GST 18", hsn="4820")]
		self.assertEqual(len(group_rows(rows, inherit_hsn=True)), 2)
		self.assertEqual(len(group_rows(rows, inherit_hsn=False)), 1)

	def test_itc_and_nature_split(self):
		rows = [_row(100, "A", itc=0), _row(100, "A", itc=1), _row(100, "A", nature="Fixed Asset")]
		self.assertEqual(len(group_rows(rows)), 3)

	def test_t07_zero_value_blocked(self):
		g = group_rows([_row(0, "A")])
		self.assertRaises(frappe.ValidationError, allocate, g, 100)
