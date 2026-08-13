import frappe


@frappe.whitelist()
def get_bootstrap():
	"""Return permission-aware identity and live CMR dashboard data."""
	return {
		"user": frappe.utils.get_fullname(frappe.session.user),
		"user_id": frappe.session.user,
		"app_name": "cmr_pipe_laying_master",
		"app_title": "CMR Pipe Laying Master",
		"version": "0.1.0",
		"company": frappe.defaults.get_user_default("Company") or frappe.defaults.get_global_default("company"),
		"financial_year": frappe.defaults.get_global_default("fiscal_year"),
		"metrics": _get_metrics(),
		"recent_activity": _get_recent_activity(),
	}


def _get_metrics():
	from frappe.utils import get_first_day, nowdate

	return {
		"pending_approvals": frappe.db.count("CMR Pipe Laying Measurement", {"status": "Pending Approval"}),
		"material_inward_this_month": frappe.db.count(
			"Purchase Receipt",
			{"docstatus": 1, "posting_date": [">=", get_first_day(nowdate())], "custom_cmr_site": ["is", "set"]},
		),
		"pipe_laying_completed": frappe.db.count("CMR Pipe Laying Measurement", {"docstatus": 1}),
		"pending_restoration": frappe.db.count(
			"CMR Pipe Segment", {"restoration_required": "Yes", "restoration_status": "Pending"}
		),
	}


def _get_recent_activity():
	rows = []
	for doctype, label, date_field in (
		("CMR Pipe Laying Measurement", "Pipe Laying", "laying_date"),
		("CMR Valve Installation", "Valve Installation", "installation_date"),
		("CMR Road Restoration", "Road Restoration", "restoration_date"),
	):
		try:
			documents = frappe.get_list(
				doctype,
				fields=["name", "project", date_field, "status", "modified"],
				order_by="modified desc",
				limit_page_length=5,
			)
		except frappe.PermissionError:
			continue
		for document in documents:
			rows.append({
				"document": label,
				"doctype": doctype,
				"reference": document.name,
				"project": document.project,
				"date": document.get(date_field),
				"status": document.status,
				"modified": document.modified,
			})
	rows.sort(key=lambda row: row["modified"], reverse=True)
	return rows[:8]