import frappe
from frappe import _
from frappe.utils import flt

from freight_charges.freight_charges.allocation import allocate, group_rows

PURCHASE_DOCTYPES = ("Purchase Order", "Purchase Invoice")


def before_validate(doc, method=None):
	"""Regenerate system-controlled freight rows from the current items."""
	if doc.docstatus != 0:
		return

	remove_auto_rows(doc)

	if not doc.get("apply_proportional_freight_gst"):
		return

	settings = frappe.get_cached_doc("Freight Settings")
	is_purchase = doc.doctype in PURCHASE_DOCTYPES
	freight_item = settings.purchase_freight_item if is_purchase else settings.sales_freight_item
	if not freight_item:
		frappe.throw(_("Please set the freight item in Freight Settings."))

	if flt(doc.get("freight_amount")) <= 0:
		frappe.throw(_("Freight Amount must be greater than zero."))

	rows = [r for r in doc.items if not r.get("is_auto_freight_row")]
	if any(r.item_code == freight_item for r in rows):
		frappe.throw(
			_("Row {0}: {1} cannot be added manually while Apply Proportional Freight GST is enabled.").format(
				rows[[r.item_code for r in rows].index(freight_item)].idx, frappe.bold(freight_item)
			)
		)
	if not rows:
		frappe.throw(_("Add items before applying proportional freight."))

	inherit_hsn = settings.freight_hsn_mode != "Freight SAC"
	item_natures = get_item_natures([r.item_code for r in rows])
	data = [
		{
			"value": flt(r.get("net_amount")) or flt(r.get("amount")),
			"item_tax_template": r.get("item_tax_template"),
			"nature": item_natures.get(r.item_code, "Non-stock"),
			"gst_hsn_code": r.get("gst_hsn_code"),
			"is_ineligible_for_itc": r.get("is_ineligible_for_itc") if is_purchase else 0,
			"row": r,
		}
		for r in rows
	]

	groups = group_rows(data, inherit_hsn=inherit_hsn, include_itc=is_purchase)
	precision = doc.precision("freight_amount") or 2
	shares = allocate(groups, flt(doc.freight_amount), precision)

	for key, group in groups.items():
		share = shares[key]
		if not share:
			continue
		src = group["first"]["row"]
		tmpl, nature, ineligible, hsn = key
		row = doc.append(
			"items",
			{
				"item_code": freight_item,
				"qty": 1,
				"rate": share,
				"is_auto_freight_row": 1,
				"freight_for": nature,
				"freight_source_group": " | ".join(
					[tmpl or "-", nature, "ITC-blocked" if ineligible else "ITC-ok", hsn or "-"]
				),
				"item_tax_template": tmpl or None,
				"cost_center": src.get("cost_center"),
				"project": src.get("project"),
				"warehouse": None,
			},
		)
		apply_row_defaults(doc, row, freight_item)
		row.rate = share
		row.price_list_rate = share
		row.amount = flt(share, precision)
		if is_purchase:
			row.is_ineligible_for_itc = ineligible
			if settings.freight_expense_account:
				row.expense_account = settings.freight_expense_account
		row.gst_hsn_code = hsn if inherit_hsn else settings.freight_sac


def apply_row_defaults(doc, row, freight_item):
	"""Fill item name, uom etc. like a normal row, without touching tax template."""
	item = frappe.get_cached_doc("Item", freight_item)
	row.item_name = item.item_name
	row.description = item.description or item.item_name
	row.uom = row.uom or item.stock_uom
	row.stock_uom = item.stock_uom
	row.conversion_factor = 1


def remove_auto_rows(doc):
	doc.set("items", [r for r in doc.items if not r.get("is_auto_freight_row")])
	for idx, row in enumerate(doc.items, start=1):
		row.idx = idx


def get_item_natures(item_codes):
	natures = {}
	if not item_codes:
		return natures
	for d in frappe.get_all(
		"Item",
		filters={"name": ("in", list(set(item_codes)))},
		fields=["name", "is_stock_item", "is_fixed_asset"],
	):
		natures[d.name] = (
			"Fixed Asset" if d.is_fixed_asset else "Stock" if d.is_stock_item else "Non-stock"
		)
	return natures
