PARENT_DOCTYPES = [
	"Purchase Order",
	"Purchase Receipt",
	"Purchase Invoice",
	"Sales Order",
	"Delivery Note",
	"Sales Invoice",
]
ITEM_DOCTYPES = [f"{d} Item" for d in PARENT_DOCTYPES]


def get_custom_fields():
	parent_fields = [
		{
			"fieldname": "proportional_freight_section",
			"fieldtype": "Section Break",
			"label": "Proportional Freight GST",
			"insert_after": "scan_barcode",
			"collapsible": 1,
		},
		{
			"fieldname": "apply_proportional_freight_gst",
			"fieldtype": "Check",
			"label": "Apply Proportional Freight GST",
			"insert_after": "proportional_freight_section",
			"no_copy": 1,
		},
		{
			"fieldname": "freight_amount",
			"fieldtype": "Currency",
			"label": "Freight Amount",
			"insert_after": "apply_proportional_freight_gst",
			"depends_on": "apply_proportional_freight_gst",
			"mandatory_depends_on": "apply_proportional_freight_gst",
			"options": "currency",
			"no_copy": 1,
		},
	]
	item_fields = [
		{
			"fieldname": "is_auto_freight_row",
			"fieldtype": "Check",
			"label": "Is Auto Freight Row",
			"insert_after": "item_code",
			"read_only": 1,
			"no_copy": 1,
			"print_hide": 1,
		},
		{
			"fieldname": "freight_for",
			"fieldtype": "Select",
			"label": "Freight For",
			"options": "\nStock\nFixed Asset\nNon-stock",
			"insert_after": "is_auto_freight_row",
			"read_only": 1,
			"no_copy": 1,
			"print_hide": 1,
			"depends_on": "is_auto_freight_row",
		},
		{
			"fieldname": "freight_source_group",
			"fieldtype": "Small Text",
			"label": "Freight Source Group",
			"insert_after": "freight_for",
			"read_only": 1,
			"no_copy": 1,
			"print_hide": 1,
			"hidden": 1,
		},
	]
	fields = {d: parent_fields for d in PARENT_DOCTYPES}
	fields.update({d: item_fields for d in ITEM_DOCTYPES})
	return fields
