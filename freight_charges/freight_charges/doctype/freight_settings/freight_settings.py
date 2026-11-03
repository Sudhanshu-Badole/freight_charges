import frappe
from frappe import _
from frappe.model.document import Document


class FreightSettings(Document):
	def validate(self):
		for field in ("purchase_freight_item", "sales_freight_item"):
			item = self.get(field)
			if item and frappe.db.get_value("Item", item, "is_stock_item"):
				frappe.throw(
					_("{0} must be a non-stock item.").format(frappe.bold(item)),
					title=_("Invalid Freight Item"),
				)
		if self.freight_hsn_mode == "Freight SAC" and not self.freight_sac:
			frappe.throw(_("Freight SAC is required when Freight HSN Mode is Freight SAC."))
