import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


ROLES = (
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
		{"fieldname": "custom_cmr_site", "label": "CMR Site", "fieldtype": "Link", "options": "CMR Site", "insert_after": "custom_cmr_details_section"},
		{"fieldname": "custom_cmr_mrn_no", "label": "MRN / GRN No", "fieldtype": "Data", "insert_after": "custom_cmr_site"},
		{"fieldname": "custom_cmr_vehicle_type", "label": "Vehicle Type", "fieldtype": "Select", "options": "Truck\nTrailer\nTempo\nPickup\nOther", "insert_after": "custom_cmr_mrn_no"},
		{"fieldname": "custom_cmr_transport_cost", "label": "Transport Cost", "fieldtype": "Currency", "insert_after": "custom_cmr_vehicle_type"},
		{"fieldname": "custom_cmr_driver_name", "label": "Driver Name / Brought By", "fieldtype": "Data", "insert_after": "custom_cmr_transport_cost"},
		{"fieldname": "custom_cmr_driver_mobile", "label": "Driver Contact Number", "fieldtype": "Data", "options": "Phone", "insert_after": "custom_cmr_driver_name"},
		{"fieldname": "custom_cmr_lr_no", "label": "LR No", "fieldtype": "Data", "insert_after": "custom_cmr_driver_mobile"},
		{"fieldname": "custom_cmr_verification_section", "label": "CMR Verification", "fieldtype": "Section Break", "insert_after": "custom_cmr_lr_no"},
		{"fieldname": "custom_cmr_qty_verified_by", "label": "Quantity Verified By", "fieldtype": "Link", "options": "User", "insert_after": "custom_cmr_verification_section"},
		{"fieldname": "custom_cmr_rates_verified_by", "label": "Rates Verified By", "fieldtype": "Link", "options": "User", "insert_after": "custom_cmr_qty_verified_by"},
		{"fieldname": "custom_cmr_class_verified_by", "label": "Class Verified By", "fieldtype": "Link", "options": "User", "insert_after": "custom_cmr_rates_verified_by"},
		{"fieldname": "custom_cmr_dimensions_verified_by", "label": "Dimensions Verified By", "fieldtype": "Link", "options": "User", "insert_after": "custom_cmr_class_verified_by"},
		{"fieldname": "custom_cmr_invoice_status", "label": "Invoice Status", "fieldtype": "Select", "options": "Pending\nPaid", "insert_after": "custom_cmr_dimensions_verified_by"},
		{"fieldname": "custom_cmr_quantity_breakup", "label": "Pipe / Roll Quantity Breakup", "fieldtype": "Table", "options": "CMR Material Quantity Breakup", "insert_after": "custom_cmr_invoice_status"},
	],
	"Purchase Receipt Item": [
		{"fieldname": "custom_cmr_material_type", "label": "CMR Material Type", "fieldtype": "Select", "options": "Pipe\nFitting\nValve\nConsumable\nOther", "insert_after": "item_name", "in_list_view": 1},
		{"fieldname": "custom_cmr_moc", "label": "MOC", "fieldtype": "Data", "insert_after": "custom_cmr_material_type"},
		{"fieldname": "custom_cmr_pressure_rating", "label": "Class / Pressure Rating", "fieldtype": "Data", "insert_after": "custom_cmr_moc"},
		{"fieldname": "custom_cmr_diameter", "label": "Diameter / Size", "fieldtype": "Float", "insert_after": "custom_cmr_pressure_rating"},
		{"fieldname": "custom_cmr_consumable_type", "label": "Consumption Type", "fieldtype": "Select", "options": "Consumable\nNon-Consumable", "insert_after": "custom_cmr_diameter"},
	],
	"Stock Entry": [
		{"fieldname": "custom_cmr_section", "label": "CMR Transfer Context", "fieldtype": "Section Break", "insert_after": "source_reference"},
		{"fieldname": "custom_cmr_site", "label": "CMR Site", "fieldtype": "Link", "options": "CMR Site", "insert_after": "custom_cmr_section"},
		{"fieldname": "custom_cmr_contractor_assignment", "label": "CMR Contractor Assignment", "fieldtype": "Link", "options": "CMR Contractor Assignment", "insert_after": "custom_cmr_site"},
		{"fieldname": "custom_cmr_transfer_context", "label": "Transfer Context", "fieldtype": "Select", "options": "Store to Store\nStore to Contractor\nContractor Return\nPipe Consumption\nValve Consumption", "insert_after": "custom_cmr_contractor_assignment"},
		{"fieldname": "custom_cmr_receiver", "label": "Receiver", "fieldtype": "Link", "options": "User", "insert_after": "custom_cmr_transfer_context"},
	],
}


def after_install():
	sync_power_app_foundation()


def after_migrate():
	sync_power_app_foundation()


@frappe.whitelist()
def sync_power_app_foundation():
	create_custom_fields(CUSTOM_FIELDS, update=True)
	_sync_roles()
	_sync_stock_entry_types()
	from cmr_pipe_laying_master.setup.permissions import sync_permissions
	from cmr_pipe_laying_master.setup.workflow import sync_workflow

	permission_count = sync_permissions()
	workflow = sync_workflow()
	frappe.clear_cache()
	return {
		"custom_fields": sum(len(fields) for fields in CUSTOM_FIELDS.values()),
		"roles": len(ROLES),
		"stock_entry_types": len(STOCK_ENTRY_TYPES),
		"custom_permissions": permission_count,
		"workflow": workflow,
	}


def _sync_roles():
	for role_name in ROLES:
		if not frappe.db.exists("Role", role_name):
			frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": 1}).insert(ignore_permissions=True)


def _sync_stock_entry_types():
	for name, purpose in STOCK_ENTRY_TYPES.items():
		if frappe.db.exists("Stock Entry Type", name):
			frappe.db.set_value("Stock Entry Type", name, "purpose", purpose)
		else:
			frappe.get_doc({"doctype": "Stock Entry Type", "name": name, "purpose": purpose, "is_standard": 0}).insert(ignore_permissions=True)
