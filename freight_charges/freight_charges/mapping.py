import frappe
from frappe.utils import flt

# target doctype -> (source link field on item row, source parent doctype)
INVOICE_SOURCES = {
	"Purchase Invoice": ("purchase_order", "Purchase Order"),
	"Sales Invoice": ("sales_order", "Sales Order"),
}
STOCK_DOCS = ("Purchase Receipt", "Delivery Note")


def after_mapping(doc, method=None, source_doc=None):
	"""Carry freight from the source order to a downstream document.

	PR / DN: keep the checkbox and amount for reference; freight rows are only
	generated on invoices so stock documents never carry freight.
	PI / SI: default the freight to the share of the source freight matching the goods billed.
	"""
	if not source_doc or not source_doc.get("apply_proportional_freight_gst"):
		return

	doc.items = [r for r in doc.items if not r.get("is_auto_freight_row")]
	for idx, row in enumerate(doc.items, start=1):
		row.idx = idx

	if doc.doctype in STOCK_DOCS:
		doc.apply_proportional_freight_gst = 1
		doc.freight_amount = source_doc.freight_amount
		return

	doc.apply_proportional_freight_gst = 1
	doc.freight_amount = scale_freight(doc, source_doc)


def scale_freight(doc, source_doc):
	"""source freight x billed goods value / source goods value, capped by what is left."""
	source_goods = sum(
		flt(r.get("net_amount")) or flt(r.get("amount"))
		for r in source_doc.items
		if not r.get("is_auto_freight_row")
	)
	billed_goods = sum(
		flt(r.get("net_amount")) or flt(r.get("amount"))
		for r in doc.items
		if not r.get("is_auto_freight_row")
	)
	if not source_goods:
		return 0

	freight = flt(source_doc.freight_amount) * billed_goods / source_goods
	order_doctype = {"Purchase Invoice": "Purchase Order", "Sales Invoice": "Sales Order"}.get(doc.doctype)
	if order_doctype and source_doc.doctype == order_doctype:
		freight = min(freight, remaining_freight(doc.doctype, source_doc))
	return flt(freight, doc.precision("freight_amount") or 2)


def remaining_freight(invoice_doctype, order):
	"""Source freight minus freight already placed on other submitted invoices of the order."""
	item_table = f"`tab{invoice_doctype} Item`"
	link = INVOICE_SOURCES[invoice_doctype][0]
	used = frappe.db.sql(
		f"""
		select coalesce(sum(inv.freight_amount), 0)
		from `tab{invoice_doctype}` inv
		where inv.docstatus = 1 and inv.apply_proportional_freight_gst = 1
		and inv.name in (select distinct parent from {item_table} where {link} = %s)
		""",
		order.name,
	)[0][0]
	return max(flt(order.freight_amount) - flt(used), 0)
