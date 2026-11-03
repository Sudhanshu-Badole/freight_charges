const freight_handlers = {
	refresh(frm) {
		set_freight_rows_readonly(frm);
		if (frm.doc.docstatus === 0 && frm.doc.apply_proportional_freight_gst) {
			frm.dashboard.set_headline_alert(
				__("Freight rows are generated automatically when the document is saved."),
				"blue"
			);
		}
	},
	apply_proportional_freight_gst(frm) {
		if (!frm.doc.apply_proportional_freight_gst) {
			frm.set_value("freight_amount", 0);
		}
	},
	items_on_form_rendered(frm) {
		set_freight_rows_readonly(frm);
	},
};

function set_freight_rows_readonly(frm) {
	const grid = frm.fields_dict.items && frm.fields_dict.items.grid;
	if (!grid || frm.doc.docstatus !== 0) return;
	(frm.doc.items || []).forEach((row) => {
		if (!row.is_auto_freight_row) return;
		const grid_row = grid.get_row(row.name);
		if (!grid_row) return;
		grid_row.wrapper.addClass("text-muted");
		grid_row.wrapper.find(".grid-delete-row, .grid-row-check").hide();
		grid_row.docfields.forEach((df) => (df.read_only = 1));
		grid_row.refresh();
	});
}

["Purchase Order", "Purchase Invoice", "Sales Order", "Sales Invoice"].forEach((dt) =>
	frappe.ui.form.on(dt, freight_handlers)
);
