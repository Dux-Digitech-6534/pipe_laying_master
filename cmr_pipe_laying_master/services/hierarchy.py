import frappe


RAISONI_SITE = "raisonigroup.duxdigitech.in"


def validate_location_hierarchy(project, site, zone, village):
	"""Validate the selected Raisoni location chain without changing other sites."""
	if frappe.local.site != RAISONI_SITE:
		return

	site_values = frappe.db.get_value("CMR Site", site, ["project", "status"], as_dict=True)
	if not site_values or site_values.project != project or site_values.status != "Active":
		frappe.throw("Selected Site does not belong to the selected Project or is inactive")

	zone_values = frappe.db.get_value("CMR Zone", zone, ["project", "site", "enabled"], as_dict=True)
	if not zone_values or zone_values.project != project or zone_values.site != site or not zone_values.enabled:
		frappe.throw("Selected Zone does not belong to the selected Project and Site or is disabled")

	village_values = frappe.db.get_value(
		"CMR Village",
		village,
		["project", "site", "zone", "enabled"],
		as_dict=True,
	)
	if (
		not village_values
		or village_values.project != project
		or village_values.site != site
		or village_values.zone != zone
		or not village_values.enabled
	):
		frappe.throw("Selected Village does not belong to the selected Project, Site and Zone or is disabled")


def validate_measurement_location(
	pipe_measurement,
	project,
	site,
	zone,
	village,
	company=None,
	contractor_assignment=None,
):
	"""Require a submitted measurement from the selected Raisoni location chain."""
	if frappe.local.site != RAISONI_SITE:
		return

	measurement = frappe.db.get_value(
		"CMR Pipe Laying Measurement",
		pipe_measurement,
		["company", "project", "site", "zone", "village", "contractor_assignment", "docstatus"],
		as_dict=True,
	)
	if (
		not measurement
		or measurement.docstatus != 1
		or measurement.project != project
		or measurement.site != site
		or measurement.zone != zone
		or measurement.village != village
		or (company is not None and measurement.company != company)
		or (
			contractor_assignment is not None
			and measurement.contractor_assignment != contractor_assignment
		)
	):
		frappe.throw("Selected Pipe Laying Measurement details do not match or the measurement is not submitted")
