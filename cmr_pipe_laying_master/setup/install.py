import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


OBSOLETE_ROLES = (
	"CMR Pipe Admin",
	"CMR Master Manager",
	"CMR Store User",
	"CMR Site Engineer",
	"CMR Project Manager",
	"CMR Pipe Viewer",
)

STOCK_ENTRY_TYPES = {
	"CMR Contractor Issue": "Material Transfer",
	"CMR Contractor Return": "Material Transfer",
	"CMR Pipe Consumption": "Material Issue",
	"CMR Valve Consumption": "Material Issue",
}

CUSTOM_FIELDS = {
	"Purchase Receipt": [
		{"fieldname": "custom_cmr_details_section", "label": "CMR Receipt Details", "fieldtype": "Section Break", "insert_after": "supplier_delivery_note"},
		{"fieldname": "custom_cmr_site", "label": "Site", "fieldtype": "Link", "options": "CMR Site", "insert_after": "custom_cmr_details_section"},
		{"fieldname": "custom_cmr_mrn_no", "label": "MRN / GRN No", "fieldtype": "Data", "insert_after": "custom_cmr_site"},
		{"fieldname": "custom_cmr_po_number", "label": "PO Number", "fieldtype": "Data", "insert_after": "custom_cmr_mrn_no"},
		{"fieldname": "custom_cmr_vehicle_type", "label": "Vehicle Type", "fieldtype": "Select", "options": "Bike\nTruck\nTrailer\nTempo\nPickup\nOther", "insert_after": "custom_cmr_po_number"},
		{"fieldname": "custom_cmr_vehicle_no", "label": "Vehicle No", "fieldtype": "Data", "insert_after": "custom_cmr_vehicle_type"},
		{"fieldname": "custom_cmr_transporter_name", "label": "Transporter Name", "fieldtype": "Data", "insert_after": "custom_cmr_vehicle_no"},
		{"fieldname": "custom_cmr_transport_cost", "label": "Transport Cost", "fieldtype": "Currency", "insert_after": "custom_cmr_transporter_name"},
		{"fieldname": "custom_cmr_driver_name", "label": "Driver Name / Brought By", "fieldtype": "Data", "insert_after": "custom_cmr_transport_cost"},
		{"fieldname": "custom_cmr_driver_mobile", "label": "Driver Contact Number", "fieldtype": "Data", "options": "Phone", "insert_after": "custom_cmr_driver_name"},
		{"fieldname": "custom_cmr_lr_no", "label": "LR No", "fieldtype": "Data", "insert_after": "custom_cmr_driver_mobile"},
		{"fieldname": "custom_cmr_invoice_no", "label": "Invoice No", "fieldtype": "Data", "insert_after": "custom_cmr_lr_no"},
		{"fieldname": "custom_cmr_invoice_date", "label": "Invoice Date", "fieldtype": "Date", "insert_after": "custom_cmr_invoice_no"},
		{"fieldname": "custom_cmr_invoice_attachment", "label": "Invoice Attachment", "fieldtype": "Attach", "insert_after": "custom_cmr_invoice_date"},
		{"fieldname": "custom_cmr_test_report_attachment", "label": "Test Report Attachment", "fieldtype": "Attach", "insert_after": "custom_cmr_invoice_attachment"},
		{"fieldname": "custom_cmr_bilty_attachment", "label": "Bilty Attachment", "fieldtype": "Attach", "insert_after": "custom_cmr_test_report_attachment"},
		{"fieldname": "custom_cmr_verification_section", "label": "CMR Verification", "fieldtype": "Section Break", "insert_after": "custom_cmr_bilty_attachment"},
		{"fieldname": "custom_cmr_qty_verified_by", "label": "Quantity Verified By", "fieldtype": "Link", "options": "User", "insert_after": "custom_cmr_verification_section"},
		{"fieldname": "custom_cmr_rates_verified_by", "label": "Rates Verified By", "fieldtype": "Link", "options": "User", "insert_after": "custom_cmr_qty_verified_by"},
		{"fieldname": "custom_cmr_class_verified_by", "label": "Class Verified By", "fieldtype": "Link", "options": "User", "insert_after": "custom_cmr_rates_verified_by"},
		{"fieldname": "custom_cmr_dimensions_verified_by", "label": "Dimensions Verified By", "fieldtype": "Link", "options": "User", "insert_after": "custom_cmr_class_verified_by"},
		{"fieldname": "custom_cmr_invoice_status", "label": "Invoice Status", "fieldtype": "Select", "options": "Pending\nReceived\nVerified\nPaid", "insert_after": "custom_cmr_dimensions_verified_by"},
		{"fieldname": "custom_cmr_quantity_breakup", "label": "Pipe / Roll Quantity Breakup", "fieldtype": "Table", "options": "CMR Material Quantity Breakup", "insert_after": "custom_cmr_invoice_status"},
	],
	"Purchase Receipt Item": [
		{"fieldname": "custom_cmr_material_type", "label": "CMR Material Type", "fieldtype": "Select", "options": "Pipe\nFitting\nValve\nOther", "insert_after": "item_name", "in_list_view": 1},
		{"fieldname": "custom_cmr_moc", "label": "MOC", "fieldtype": "Data", "insert_after": "custom_cmr_material_type"},
		{"fieldname": "custom_cmr_pressure_rating", "label": "Class / Pressure Rating", "fieldtype": "Data", "insert_after": "custom_cmr_moc"},
		{"fieldname": "custom_cmr_diameter", "label": "Diameter / Size", "fieldtype": "Float", "insert_after": "custom_cmr_pressure_rating"},
		{"fieldname": "custom_cmr_consumable_type", "label": "Consumption Type", "fieldtype": "Select", "options": "Consumable\nNon-Consumable", "insert_after": "custom_cmr_diameter"},
	],
	"Item": [
		{"fieldname": "custom_cmr_material_type", "label": "Material Type", "fieldtype": "Select", "options": "Pipe\nFitting\nValve\nOther", "insert_after": "item_name"},
		{"fieldname": "custom_cmr_moc", "label": "MOC", "fieldtype": "Select", "options": "HDPE\nDI\nMS\nuPVC\nCI", "insert_after": "custom_cmr_material_type"},
		{"fieldname": "custom_cmr_pressure_rating", "label": "Class / Pressure Rating", "fieldtype": "Select", "options": "PN6\nPN10\nPN16\nK9", "insert_after": "custom_cmr_moc"},
		{"fieldname": "custom_cmr_diameter", "label": "Diameter / Size", "fieldtype": "Float", "insert_after": "custom_cmr_pressure_rating"},
	],
	"Stock Entry": [
		{"fieldname": "custom_cmr_section", "label": "CMR Transfer Context", "fieldtype": "Section Break", "insert_after": "source_reference"},
		{"fieldname": "custom_cmr_site", "label": "Site", "fieldtype": "Link", "options": "CMR Site", "insert_after": "custom_cmr_section"},
		{"fieldname": "custom_cmr_contractor_assignment", "label": "Contractor Assignment", "fieldtype": "Link", "options": "CMR Contractor Assignment", "insert_after": "custom_cmr_site"},
		{"fieldname": "custom_cmr_transfer_context", "label": "Transfer Context", "fieldtype": "Select", "options": "Store to Store\nStore to Contractor\nContractor Return\nPipe Consumption\nValve Consumption", "insert_after": "custom_cmr_contractor_assignment"},
		{"fieldname": "custom_cmr_receiver", "label": "Receiver", "fieldtype": "Link", "options": "User", "insert_after": "custom_cmr_transfer_context"},
	],
}


def after_install():
	sync_power_app_foundation()


def after_migrate():
	sync_power_app_foundation()


def sync_power_app_foundation():
	create_custom_fields(CUSTOM_FIELDS, update=True)
	_sync_stock_entry_types()
	from cmr_pipe_laying_master.services.hierarchy import RAISONI_SITE
	from cmr_pipe_laying_master.setup.workflow import disable_workflow, sync_workflow
	workflow = disable_workflow() if frappe.local.site == RAISONI_SITE else sync_workflow()
	valve_gps = configure_raisoni_valve_gps()
	cleanup = remove_obsolete_role_configuration()
	frappe.clear_cache()
	return {
		"custom_fields": sum(len(fields) for fields in CUSTOM_FIELDS.values()),
		"stock_entry_types": len(STOCK_ENTRY_TYPES),
		"workflow": workflow,
		"valve_gps": valve_gps,
		"obsolete_role_cleanup": cleanup,
	}


def configure_raisoni_valve_gps():
	"""Allow Raisoni Valve drafts without GPS; submit validation remains authoritative."""
	from cmr_pipe_laying_master.services.hierarchy import RAISONI_SITE

	if frappe.local.site != RAISONI_SITE:
		return {"updated": False, "reason": "not Raisoni"}

	from frappe.custom.doctype.property_setter.property_setter import make_property_setter

	updated = []
	for fieldname in ("gps_latitude", "gps_longitude"):
		filters = {
			"doc_type": "CMR Valve Installation",
			"field_name": fieldname,
			"property": "reqd",
		}
		name = frappe.db.get_value("Property Setter", filters, "name")
		if name:
			frappe.db.set_value("Property Setter", name, "value", "0")
		else:
			make_property_setter(
				"CMR Valve Installation",
				fieldname,
				"reqd",
				0,
				"Check",
				is_system_generated=True,
			)
		updated.append(fieldname)

	frappe.clear_cache(doctype="CMR Valve Installation")
	return {"updated": True, "fields": updated}


def create_raisoni_trial_materials():
	"""Create a small, clearly named Raisoni-only data set for Material Inward testing."""
	from cmr_pipe_laying_master.services.hierarchy import RAISONI_SITE

	if frappe.local.site != RAISONI_SITE:
		return {"created": [], "updated": [], "reason": "not Raisoni"}

	attributes = {
		"Material Type": ("Pipe", "Fitting", "Valve"),
		"MOC": ("HDPE", "DI", "MS", "uPVC"),
		"Class": ("PN6", "PN10", "PN16", "K9"),
		"Size": ("63", "90", "100", "110", "160"),
	}
	for attribute_name, values in attributes.items():
		name = frappe.db.get_value("Item Attribute", {"attribute_name": attribute_name}, "name")
		doc = frappe.get_doc("Item Attribute", name) if name else frappe.new_doc("Item Attribute")
		if not name:
			doc.attribute_name = attribute_name
			doc.numeric_values = 0
		existing = {row.attribute_value for row in doc.item_attribute_values}
		for value in values:
			if value not in existing:
				doc.append("item_attribute_values", {"attribute_value": value, "abbr": value[:10]})
		doc.save(ignore_permissions=True) if name else doc.insert(ignore_permissions=True)

	item_group = "Products" if frappe.db.exists("Item Group", "Products") else frappe.db.get_value("Item Group", {"is_group": 0}, "name")
	default_uom = "Nos" if frappe.db.exists("UOM", "Nos") else frappe.db.get_value("UOM", {}, "name")
	roll_uom = "Meter" if frappe.db.exists("UOM", "Meter") else default_uom
	trial_items = (
		("CMR-TRIAL-HDPE-PIPE-110", "Trial HDPE Pipe 110 mm", "Pipe", "HDPE", "PN10", 110, default_uom),
		("CMR-TRIAL-HDPE-ROLL-63", "Trial HDPE Pipe Roll 63 mm", "Pipe", "HDPE", "PN6", 63, roll_uom),
		("CMR-TRIAL-DI-PIPE-100", "Trial DI Pipe 100 mm", "Pipe", "DI", "K9", 100, default_uom),
		("CMR-TRIAL-DI-BEND-100", "Trial DI Bend 100 mm", "Fitting", "DI", "K9", 100, default_uom),
		("CMR-TRIAL-HDPE-ROLL-90", "Trial HDPE Pipe Roll 90 mm", "Pipe", "HDPE", "PN10", 90, roll_uom),
		("CMR-TRIAL-HDPE-ROLL-110", "Trial HDPE Pipe Roll 110 mm", "Pipe", "HDPE", "PN16", 110, roll_uom),
		("CMR-TRIAL-UPVC-PIPE-160", "Trial uPVC Pipe 160 mm", "Pipe", "uPVC", "PN6", 160, default_uom),
		("CMR-TRIAL-MS-PIPE-100", "Trial MS Pipe 100 mm", "Pipe", "MS", "PN10", 100, default_uom),
	)
	created, updated = [], []
	for item_code, item_name, material_type, moc, pressure_rating, diameter, stock_uom in trial_items:
		is_new = not frappe.db.exists("Item", item_code)
		doc = frappe.new_doc("Item") if is_new else frappe.get_doc("Item", item_code)
		if is_new:
			doc.item_code = item_code
			doc.item_group = item_group
			doc.is_stock_item = 1
		doc.item_name = item_name
		doc.stock_uom = stock_uom
		doc.description = "Raisoni CMR Pipe Laying trial item"
		for fieldname, value in {
			"custom_cmr_material_type": material_type,
			"custom_cmr_moc": moc,
			"custom_cmr_pressure_rating": pressure_rating,
			"custom_cmr_diameter": diameter,
		}.items():
			if doc.meta.has_field(fieldname):
				doc.set(fieldname, value)
		if is_new:
			doc.insert(ignore_permissions=True)
			created.append(item_code)
		else:
			doc.save(ignore_permissions=True)
			updated.append(item_code)
	frappe.db.commit()
	frappe.clear_cache()
	return {"created": created, "updated": updated, "attributes": attributes}

def remove_obsolete_role_configuration():
	"""Remove the unapproved CMR roles and the permissions created for them."""
	custom_permissions = frappe.get_all(
		"Custom DocPerm",
		filters={"role": ["in", OBSOLETE_ROLES]},
		pluck="name",
	)
	for name in custom_permissions:
		frappe.delete_doc("Custom DocPerm", name, force=True, ignore_permissions=True)

	removed_roles = []
	for role_name in OBSOLETE_ROLES:
		frappe.db.delete("Has Role", {"role": role_name})
		if frappe.db.exists("Role", role_name):
			frappe.delete_doc("Role", role_name, force=True, ignore_permissions=True)
			removed_roles.append(role_name)

	frappe.clear_cache()
	return {
		"custom_permissions_removed": len(custom_permissions),
		"roles_removed": removed_roles,
	}


def _sync_stock_entry_types():
	for name, purpose in STOCK_ENTRY_TYPES.items():
		if frappe.db.exists("Stock Entry Type", name):
			frappe.db.set_value("Stock Entry Type", name, "purpose", purpose)
		else:
			frappe.get_doc({"doctype": "Stock Entry Type", "name": name, "purpose": purpose, "is_standard": 0}).insert(ignore_permissions=True)
