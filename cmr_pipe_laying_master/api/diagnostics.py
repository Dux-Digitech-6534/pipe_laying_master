import frappe

from cmr_pipe_laying_master.setup.install import ROLES, STOCK_ENTRY_TYPES


EXPECTED_DOCTYPES = (
	"CMR Material Quantity Breakup", "CMR Pipe Segment", "CMR Excavation Detail",
	"CMR Refill Detail", "CMR Fitting Consumption", "CMR Valve Fitting Item",
	"CMR Site", "CMR Contractor Assignment", "CMR Pipe Laying Measurement",
	"CMR Valve Installation", "CMR Road Restoration",
)


def get_power_app_foundation_status():
	return {
		"doctypes": {name: bool(frappe.db.exists("DocType", name)) for name in EXPECTED_DOCTYPES},
		"custom_fields": frappe.db.count("Custom Field", {"fieldname": ["like", "custom_cmr_%"]}),
		"roles": {name: bool(frappe.db.exists("Role", name)) for name in ROLES},
		"stock_entry_types": {name: frappe.db.get_value("Stock Entry Type", name, "purpose") for name in STOCK_ENTRY_TYPES},
		"workflow": bool(frappe.db.exists("Workflow", "CMR Pipe Laying Approval")),
		"custom_permissions": frappe.db.count("Custom DocPerm", {"role": ["in", list(ROLES)]}),
	}


def test_calculations():
	doc = frappe.get_doc({
		"doctype": "CMR Pipe Laying Measurement", "restoration_required": "Yes",
		"segments": [{"pipe_no": "TEST-PIPE-1", "actual_length": 120, "restoration_required": "Yes"}],
		"excavation_details": [{
			"excavation_type": "Excavation Ordinary Soil", "length": 120, "width": 0.8,
			"calculated_depth": 1.0, "actual_depth": 1.2,
		}],
		"refill_details": [{"material": "Sand", "length": 120, "width": 0.8, "depth": 0.3}],
	})
	doc.validate()
	return {
		"total_actual_length": doc.total_actual_length,
		"total_excavation_qty": doc.total_excavation_qty,
		"total_refill_qty": doc.total_refill_qty,
		"segment_restoration_status": doc.segments[0].restoration_status,
	}
