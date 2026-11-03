from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from freight_charges.setup.custom_fields import get_custom_fields


def after_install():
	setup_custom_fields()


def after_migrate():
	setup_custom_fields()


def setup_custom_fields():
	create_custom_fields(get_custom_fields(), update=True)
