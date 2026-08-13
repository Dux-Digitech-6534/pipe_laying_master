import json

import frappe
from frappe.model.workflow import apply_workflow
from frappe.utils import flt, getdate


@frappe.whitelist()
def get_entry_options():
	if frappe.session.user == "Guest":
		frappe.throw("Please sign in to use CMR entry forms", frappe.PermissionError)
	return {
		"companies": _list("Company", ["name"]),
		"projects": _list("Project", ["name", "project_name"], {"status": "Open"}),
		"sites": _all("CMR Site", ["name", "site_name", "company", "project", "zone", "village", "default_warehouse"], {"status": "Active"}),
		"suppliers": _list("Supplier", ["name", "supplier_name"]),
		"warehouses": _list("Warehouse", ["name", "warehouse_name", "company"], {"is_group": 0}),
		"items": _list("Item", ["name", "item_code", "item_name", "stock_uom"], {"disabled": 0, "is_stock_item": 1}, 1000),
		"contractors": _list("CMR Contractor Assignment", ["name", "contractor", "company", "project", "site", "contractor_warehouse"], {"active": 1}),
		"measurements": _list("CMR Pipe Laying Measurement", ["name", "company", "project", "site", "zone", "village", "contractor_assignment"], {"docstatus": 1}),
		"users": _list("User", ["name", "full_name"], {"enabled": 1}),
	}


@frappe.whitelist()
def save_entry(entry_type, payload, action="draft"):
	if frappe.session.user == "Guest":
		frappe.throw("Please sign in to create an entry", frappe.PermissionError)
	data = json.loads(payload) if isinstance(payload, str) else payload
	builders = {
		"material-inward": _build_purchase_receipt,
		"material-issue": lambda values: _build_stock_entry(values, False),
		"material-return": lambda values: _build_stock_entry(values, True),
		"pipe-laying": _build_pipe_measurement,
		"valves": _build_valve_installation,
		"restoration": _build_restoration,
	}
	if entry_type not in builders:
		frappe.throw("Unsupported CMR entry type")
	doc = builders[entry_type](data)
	doc.insert()

	if action == "submit":
		if entry_type == "pipe-laying":
			doc = apply_workflow(doc, "Send for Approval")
		else:
			doc.submit()

	return {
		"name": doc.name,
		"doctype": doc.doctype,
		"docstatus": doc.docstatus,
		"status": doc.get("status"),
	}


def _list(doctype, fields, filters=None, limit=500):
	try:
		return frappe.get_list(doctype, fields=fields, filters=filters or {}, order_by="modified desc", limit_page_length=limit)
	except frappe.PermissionError:
		return []


def _all(doctype, fields, filters=None, limit=500):
	return frappe.get_all(doctype, fields=fields, filters=filters or {}, order_by="modified desc", limit_page_length=limit)


def _required(data, *fields):
	missing = [field.replace("_", " ").title() for field in fields if not data.get(field)]
	if missing:
		frappe.throw(f"Please fill: {', '.join(missing)}")


def _positive_items(rows):
	items = [row for row in (rows or []) if row.get("item_code") and flt(row.get("qty")) > 0]
	if not items:
		frappe.throw("Add at least one item with a positive quantity")
	return items


def _item_values(item_code, qty, warehouse, rate=0):
	item = frappe.get_cached_doc("Item", item_code)
	return {
		"item_code": item_code,
		"item_name": item.item_name,
		"qty": flt(qty),
		"uom": item.stock_uom,
		"stock_uom": item.stock_uom,
		"conversion_factor": 1,
		"warehouse": warehouse,
		"rate": flt(rate),
	}


def _build_purchase_receipt(data):
	_required(data, "company", "supplier", "posting_date", "site", "warehouse")
	transport_cost = flt(data.get("transport_cost"))
	if transport_cost < 0:
		frappe.throw("Transport Cost cannot be negative")
	doc = frappe.new_doc("Purchase Receipt")
	doc.company = data["company"]
	doc.supplier = data["supplier"]
	doc.posting_date = getdate(data["posting_date"])
	doc.set_warehouse = data["warehouse"]
	doc.supplier_delivery_note = data.get("supplier_delivery_note")
	doc.remarks = data.get("remarks")
	doc.custom_cmr_site = data["site"]
	doc.custom_cmr_mrn_no = data.get("mrn_no")
	doc.custom_cmr_vehicle_type = data.get("vehicle_type")
	doc.custom_cmr_transport_cost = transport_cost
	doc.custom_cmr_driver_name = data.get("driver_name")
	doc.custom_cmr_driver_mobile = data.get("driver_mobile")
	doc.custom_cmr_lr_no = data.get("lr_no")
	doc.custom_cmr_invoice_status = data.get("invoice_status") or "Pending"
	if doc.meta.has_field("source_app"):
		doc.source_app = "CMR Pipe Laying Master"
	for row in _positive_items(data.get("items")):
		values = _item_values(row["item_code"], row["qty"], data["warehouse"], row.get("rate"))
		values.update({
			"custom_cmr_material_type": row.get("material_type"),
			"custom_cmr_moc": row.get("moc"),
			"custom_cmr_pressure_rating": row.get("pressure_rating"),
			"custom_cmr_diameter": flt(row.get("diameter")),
			"custom_cmr_consumable_type": row.get("consumable_type"),
		})
		doc.append("items", values)
	return doc


def _build_stock_entry(data, is_return):
	_required(data, "company", "posting_date", "site", "source_warehouse", "target_warehouse")
	doc = frappe.new_doc("Stock Entry")
	doc.stock_entry_type = "CMR Contractor Return" if is_return else "CMR Contractor Issue"
	doc.purpose = "Material Transfer"
	doc.company = data["company"]
	doc.posting_date = getdate(data["posting_date"])
	doc.project = data.get("project")
	doc.from_warehouse = data["source_warehouse"]
	doc.to_warehouse = data["target_warehouse"]
	doc.remarks = data.get("remarks")
	doc.custom_cmr_site = data["site"]
	doc.custom_cmr_contractor_assignment = data.get("contractor_assignment")
	doc.custom_cmr_transfer_context = "Contractor Return" if is_return else "Store to Contractor"
	for row in _positive_items(data.get("items")):
		values = _item_values(row["item_code"], row["qty"], data["target_warehouse"])
		values.pop("warehouse", None)
		values.pop("rate", None)
		values.update({"s_warehouse": data["source_warehouse"], "t_warehouse": data["target_warehouse"]})
		doc.append("items", values)
	return doc


def _assignment(data):
	_required(data, "contractor_assignment")
	assignment = frappe.get_doc("CMR Contractor Assignment", data["contractor_assignment"])
	if not assignment.contractor_warehouse:
		frappe.throw("Selected contractor assignment has no contractor warehouse")
	return assignment


def _build_pipe_measurement(data):
	_required(data, "company", "project", "site", "zone", "village", "laying_date", "type_of_work", "pipe_width")
	assignment = _assignment(data)
	doc = frappe.new_doc("CMR Pipe Laying Measurement")
	for field in ("company", "project", "site", "zone", "village", "laying_date", "type_of_work", "laying_mode", "trench_method", "section_incharge", "restoration_required", "end_cap", "remarks"):
		doc.set(field, data.get(field))
	doc.contractor_assignment = assignment.name
	doc.contractor_warehouse = assignment.contractor_warehouse
	doc.pipe_width = flt(data.get("pipe_width"))
	for row in data.get("segments") or []:
		if row.get("pipe_item") and flt(row.get("actual_length")) > 0:
			doc.append("segments", row)
	for row in data.get("excavation_details") or []:
		if row.get("excavation_type") and flt(row.get("length")) > 0:
			doc.append("excavation_details", row)
	for row in data.get("refill_details") or []:
		if row.get("material_type") and flt(row.get("depth")) > 0:
			doc.append("refill_details", row)
	for row in data.get("fittings") or []:
		if row.get("item_code") and flt(row.get("quantity")) > 0:
			doc.append("fittings", row)
	return doc


def _build_valve_installation(data):
	_required(data, "company", "project", "site", "zone", "village", "installation_date", "pipe_measurement", "pipe_no", "valve_item", "quantity", "chamber_size", "gps_latitude", "gps_longitude")
	assignment = _assignment(data)
	doc = frappe.new_doc("CMR Valve Installation")
	for field in ("company", "project", "site", "zone", "village", "installation_date", "pipe_measurement", "pipe_no", "valve_item", "uom", "chamber_size", "specific_location", "gps_latitude", "gps_longitude", "remarks"):
		doc.set(field, data.get(field))
	doc.quantity = flt(data.get("quantity"))
	doc.contractor_assignment = assignment.name
	doc.contractor_warehouse = assignment.contractor_warehouse
	for row in data.get("fittings") or []:
		if row.get("item_code") and flt(row.get("quantity")) > 0:
			doc.append("fittings", row)
	return doc


def _build_restoration(data):
	_required(data, "company", "project", "site", "zone", "village", "restoration_date", "pipe_measurement", "pipe_no", "pipe_length", "pipe_width", "restoration_type")
	assignment = _assignment(data)
	doc = frappe.new_doc("CMR Road Restoration")
	for field in ("company", "project", "site", "zone", "village", "restoration_date", "pipe_measurement", "pipe_no", "restoration_type", "remarks"):
		doc.set(field, data.get(field))
	doc.contractor_assignment = assignment.name
	for field in ("pipe_length", "pipe_width", "m15_length", "m15_depth", "m20_length", "m20_depth", "m30_length", "m30_depth", "gps_latitude_from", "gps_longitude_from", "gps_latitude_to", "gps_longitude_to"):
		doc.set(field, flt(data.get(field)))
	return doc
