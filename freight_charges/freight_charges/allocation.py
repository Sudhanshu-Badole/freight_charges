"""Pure allocation logic: no database access, so it is easy to unit test."""

from collections import OrderedDict

import frappe
from frappe import _
from frappe.utils import flt


def group_rows(rows, inherit_hsn=True, include_itc=True):
	"""Group eligible item rows. Each row is a dict-like with value, item_tax_template,
	nature, gst_hsn_code, is_ineligible_for_itc. Returns an OrderedDict key -> group."""
	groups = OrderedDict()
	for row in rows:
		key = (
			row.get("item_tax_template") or "",
			row.get("nature") or "Non-stock",
			int(bool(row.get("is_ineligible_for_itc"))) if include_itc else 0,
			(row.get("gst_hsn_code") or "") if inherit_hsn else "",
		)
		group = groups.setdefault(key, {"key": key, "value": 0.0, "first": row})
		group["value"] += flt(row.get("value"))
	return groups


def allocate(groups, freight_amount, precision=2):
	"""Return {key: share}. Shares are rounded; the rounding difference goes to the
	largest group so the total equals the freight amount exactly."""
	total = sum(g["value"] for g in groups.values())
	if total <= 0:
		frappe.throw(_("Total eligible item value is zero, cannot allocate freight."))

	shares = {k: flt(g["value"] / total * freight_amount, precision) for k, g in groups.items()}
	diff = flt(freight_amount - sum(shares.values()), precision)
	if diff:
		largest = max(groups, key=lambda k: groups[k]["value"])
		shares[largest] = flt(shares[largest] + diff, precision)
	return shares
