from collections import defaultdict
import json

import frappe
from frappe.model.workflow import apply_workflow
from frappe.utils import cint, flt, getdate
from erpnext.stock.utils import get_stock_balance


ENTRY_EDIT_SITE = "raisonigroup.duxdigitech.in"
ENTRY_DOCTYPES = {
	"material-inward": "Purchase Receipt",
	"material-issue": "Stock Entry",
	"material-return": "Stock Entry",
	"pipe-laying": "CMR Pipe Laying Measurement",
	"valves": "CMR Valve Installation",
	"restoration": "CMR Road Restoration",
}


@frappe.whitelist()
def get_entry_options():
	if frappe.session.user == "Guest":
		frappe.throw("Please sign in to use CMR entry forms", frappe.PermissionError)
	return {
		"companies": _list("Company", ["name"]),
		"projects": _list("Project", ["name", "project_name"], {"status": "Open"}),
		"sites": _all("CMR Site", ["name", "site_name", "company", "project", "zone", "village", "default_warehouse"], {"status": "Active"}),
		"zones": _hierarchy_options("CMR Zone", ["name", "zone_name", "project", "site", "enabled"]),
		"villages": _hierarchy_options("CMR Village", ["name", "village_name", "project", "site", "zone", "enabled"]),
		"suppliers": _list("Supplier", ["name", "supplier_name"]),
		"warehouses": _list("Warehouse", ["name", "warehouse_name", "company"], {"is_group": 0}),
		"items": _item_catalog(),
		"item_attributes": _item_attribute_options(),
		"select_options": _select_field_options(),
		"contractors": _list("CMR Contractor Assignment", ["name", "contractor", "company", "project", "site", "contractor_warehouse"], {"active": 1}),
		"measurements": _list("CMR Pipe Laying Measurement", ["name", "company", "project", "site", "zone", "village", "contractor_assignment"], {"docstatus": 1}),
		"users": _list("User", ["name", "full_name"], {"enabled": 1}),
		"purchase_orders": _list(
			"Purchase Order", ["name", "supplier", "company", "transaction_date", "status"],
			{"docstatus": 1, "status": ["not in", ["Closed", "Completed", "Cancelled"]]},
		),
		"purchase_tax_templates": _list(
			"Purchase Taxes and Charges Template", ["name", "title", "company", "disabled"],
			{"disabled": 0},
		),
		"purchase_receipts": _list(
			"Purchase Receipt", ["name", "supplier", "posting_date", "company", "project", "custom_cmr_site", "set_warehouse"],
			{"docstatus": 1, "is_return": 0, "custom_cmr_site": ["is", "set"]},
		),
	}


def _submitted_material_inward(purchase_receipt):
	if not purchase_receipt:
		frappe.throw("Select a Material Inward / Purchase Receipt")
	doc = frappe.get_doc("Purchase Receipt", purchase_receipt)
	doc.check_permission("read")
	if doc.docstatus != 1 or cint(doc.is_return) or not doc.get("custom_cmr_site"):
		frappe.throw("Select a submitted CMR Material Inward / Purchase Receipt")
	return doc


def _material_inward_warehouse(doc):
	warehouses = {row.warehouse or doc.set_warehouse for row in doc.items if row.item_code and (row.warehouse or doc.set_warehouse)}
	if len(warehouses) != 1:
		frappe.throw("Selected Material Inward must contain items from one Receiving Warehouse")
	return next(iter(warehouses))


@frappe.whitelist()
def get_material_inward_items(purchase_receipt):
	"""Load submitted Material Inward rows without bypassing Purchase Receipt permissions."""
	_check_entry_user()
	_check_entry_edit_site()
	doc = _submitted_material_inward(purchase_receipt)
	warehouse = _material_inward_warehouse(doc)
	items = []
	for row in doc.items:
		if not row.item_code:
			continue
		metadata = _item_metadata(row.item_code)
		items.append({
			"item_code": row.item_code,
			"qty": flt(row.stock_qty or row.qty, 3),
			"rate": 0,
			"uom": row.stock_uom or row.uom,
			"material_type": metadata.material_type,
			"moc": metadata.moc,
			"pressure_rating": metadata.pressure_rating,
			"diameter": metadata.diameter,
			"consumable_type": row.get("custom_cmr_consumable_type") or "Consumable",
			"source_stock": flt(get_stock_balance(row.item_code, warehouse), 3),
			"target_stock": 0,
		})
	return {
		"purchase_receipt": doc.name,
		"supplier": doc.supplier,
		"posting_date": doc.posting_date,
		"company": doc.company,
		"project": doc.project,
		"site": doc.custom_cmr_site,
		"source_warehouse": warehouse,
		"items": items,
	}


@frappe.whitelist()
def get_purchase_order_items(purchase_order):
	"""Return pending native Purchase Order rows for portal Purchase Receipt creation."""
	_check_entry_user()
	order = frappe.get_doc("Purchase Order", purchase_order)
	order.check_permission("read")
	if order.docstatus != 1 or order.status in ("Closed", "Completed", "Cancelled"):
		frappe.throw("Select an open Submitted Purchase Order")
	return [{
		"purchase_order": order.name,
		"purchase_order_item": row.name,
		"item_code": row.item_code,
		"qty": max(flt(row.qty) - flt(row.received_qty), 0),
		"rate": flt(row.rate),
		"uom": row.uom,
		"warehouse": row.warehouse,
	} for row in order.items if row.item_code and flt(row.qty) - flt(row.received_qty) > 0]


@frappe.whitelist()
def get_warehouse_stock(item_code, warehouse):
	"""Read live stock from ERPNext's Stock Ledger/Bin calculation."""
	_check_entry_user()
	if not item_code or not warehouse:
		return 0
	return flt(get_stock_balance(item_code, warehouse), 3)


@frappe.whitelist()
def get_measurement_segments(pipe_measurement, purpose=""):
	"""Return eligible segments from a submitted measurement after checking read access."""
	_check_entry_user()
	_check_entry_edit_site()
	purpose = (purpose or "").strip().lower()
	if purpose not in ("", "valve", "restoration"):
		frappe.throw("Unsupported measurement segment purpose")

	measurement = frappe.get_doc("CMR Pipe Laying Measurement", pipe_measurement)
	measurement.check_permission("read")
	if measurement.docstatus != 1:
		frappe.throw("Only Submitted Pipe Laying Measurements can be selected")

	segments = []
	for row in measurement.segments:
		if not row.pipe_no:
			continue
		if purpose == "restoration" and (
			not cint(row.restoration_required) or row.restoration_status in ("Not Required", "Completed")
		):
			continue
		segments.append({
			"name": row.name,
			"pipe_no": row.pipe_no,
			"pipe_item": row.pipe_item,
			"start_node": row.start_node,
			"end_node": row.end_node,
			"actual_length": flt(row.actual_length),
			"valve_status": row.valve_status,
			"restoration_required": cint(row.restoration_required),
			"restoration_status": row.restoration_status,
		})
	return segments

@frappe.whitelist()
def get_entry_records(entry_type, search="", status="", start=0, page_length=50):
	if frappe.session.user == "Guest":
		frappe.throw("Please sign in to view CMR records", frappe.PermissionError)
	configs = {
		"material-inward": {"doctype": "Purchase Receipt", "fields": ["name", "supplier", "posting_date", "company", "custom_cmr_site", "grand_total", "docstatus"], "filters": {"custom_cmr_site": ["is", "set"], "is_return": 0}, "search_fields": ["name", "supplier", "custom_cmr_site"]},
		"material-issue": {"doctype": "Stock Entry", "fields": ["name", "posting_date", "company", "custom_cmr_site", "docstatus"], "filters": {"stock_entry_type": "CMR Contractor Issue"}, "search_fields": ["name", "custom_cmr_site"]},
		"material-return": {"doctype": "Stock Entry", "fields": ["name", "posting_date", "company", "custom_cmr_site", "docstatus"], "filters": {"stock_entry_type": "CMR Contractor Return"}, "search_fields": ["name", "custom_cmr_site"]},
		"pipe-laying": {"doctype": "CMR Pipe Laying Measurement", "fields": ["name", "project", "site", "laying_date", "docstatus"], "filters": {}, "search_fields": ["name", "project", "site"]},
		"valves": {"doctype": "CMR Valve Installation", "fields": ["name", "project", "site", "installation_date", "docstatus"], "filters": {}, "search_fields": ["name", "project", "site"]},
		"restoration": {"doctype": "CMR Road Restoration", "fields": ["name", "project", "site", "restoration_date", "docstatus"], "filters": {}, "search_fields": ["name", "project", "site"]},
	}
	if entry_type not in configs:
		frappe.throw("Unsupported CMR entry list")
	config = configs[entry_type]
	doctype = config["doctype"]
	filters = dict(config["filters"])
	if str(status) in ("0", "1", "2"):
		filters["docstatus"] = int(status)
	search = (search or "").strip()
	or_filters = [[doctype, field, "like", f"%{search}%"] for field in config["search_fields"]] if search else []
	rows = frappe.get_list(doctype, fields=config["fields"], filters=filters, or_filters=or_filters, order_by="modified desc", start=max(int(start or 0), 0), page_length=min(max(int(page_length or 50), 1), 200))
	for row in rows:
		row["doctype"] = doctype
	total = len(frappe.get_list(doctype, fields=["name"], filters=filters, or_filters=or_filters, limit_page_length=100000))
	return {"records": rows, "total": total}


REPORT_CONFIGS = {
	"pipe-register": {
		"doctype": "CMR Pipe Laying Measurement",
		"fields": ["name", "project", "site", "laying_date", "type_of_work", "contractor_assignment", "status"],
		"filters": {"docstatus": 1},
		"search_fields": ["name", "project", "site"],
	},
	"valve-register": {
		"doctype": "CMR Valve Installation",
		"fields": ["name", "project", "site", "installation_date", "valve_item", "quantity", "status"],
		"filters": {"docstatus": 1},
		"search_fields": ["name", "project", "site"],
	},
	"restoration-register": {
		"doctype": "CMR Road Restoration",
		"fields": ["name", "project", "site", "restoration_date", "restoration_type", "status"],
		"filters": {"docstatus": 1},
		"search_fields": ["name", "project", "site"],
	},
}


@frappe.whitelist()
def get_report_records(report_type, search="", start=0, page_length=50):
	if frappe.session.user == "Guest":
		frappe.throw("Please sign in to view CMR reports", frappe.PermissionError)
	if report_type in ("material-stock", "contractor-stock"):
		return _stock_report(report_type, search, start, page_length)
	if report_type == "material-movement":
		return _material_movement_report(search, start, page_length)
	if report_type not in REPORT_CONFIGS:
		frappe.throw("Unsupported CMR report")
	config = REPORT_CONFIGS[report_type]
	doctype = config["doctype"]
	search = (search or "").strip()
	or_filters = [[doctype, field, "like", f"%{search}%"] for field in config["search_fields"]] if search else []
	rows = frappe.get_list(
		doctype, fields=config["fields"], filters=config["filters"], or_filters=or_filters,
		order_by="modified desc", start=max(int(start or 0), 0), page_length=min(max(int(page_length or 50), 1), 200),
	)
	total = len(frappe.get_list(doctype, fields=["name"], filters=config["filters"], or_filters=or_filters, limit_page_length=100000))
	if report_type == "pipe-register" and rows:
		assignment_ids = list({row.get("contractor_assignment") for row in rows if row.get("contractor_assignment")})
		contractor_names = {
			assignment.name: assignment.contractor
			for assignment in frappe.get_all("CMR Contractor Assignment", fields=["name", "contractor"], filters={"name": ["in", assignment_ids]})
		} if assignment_ids else {}
		for row in rows:
			row["contractor_assignment"] = contractor_names.get(row.get("contractor_assignment"), row.get("contractor_assignment"))
	return {"records": rows, "total": total}


def _material_movement_report(search, start, page_length):
	"""Flattened one-row-per-item view of contractor Issue/Return stock movements
	(a single Stock Entry can carry several items, which a header-only list would hide)."""
	entries = frappe.get_all(
		"Stock Entry", fields=["name", "stock_entry_type", "posting_date", "custom_cmr_site", "from_warehouse", "to_warehouse"],
		filters={"stock_entry_type": ["in", ["CMR Contractor Issue", "CMR Contractor Return"]]},
		order_by="modified desc", limit_page_length=0,
	)
	if not entries:
		return {"records": [], "total": 0}
	by_name = {entry.name: entry for entry in entries}
	details = frappe.get_all(
		"Stock Entry Detail", fields=["parent", "item_code", "qty", "uom"],
		filters={"parent": ["in", list(by_name)]}, order_by="parent, idx",
	)
	item_names = {}
	if details:
		item_names = {
			item.name: item.item_name
			for item in frappe.get_all("Item", fields=["name", "item_name"], filters={"name": ["in", list({detail.item_code for detail in details})]})
		}
	rows = []
	for detail in details:
		header = by_name.get(detail.parent)
		if not header:
			continue
		row = dict(header)
		row["item_code"] = detail.item_code
		row["item_name"] = item_names.get(detail.item_code, "")
		row["qty"] = detail.qty
		row["uom"] = detail.uom
		rows.append(row)
	search = (search or "").strip().lower()
	if search:
		rows = [
			row for row in rows
			if search in (row.get("name") or "").lower()
			or search in (row.get("custom_cmr_site") or "").lower()
			or search in (row.get("item_code") or "").lower()
			or search in (row.get("item_name") or "").lower()
		]
	total = len(rows)
	start = max(int(start or 0), 0)
	page_length = min(max(int(page_length or 50), 1), 200)
	return {"records": rows[start : start + page_length], "total": total}


def _stock_report(report_type, search, start, page_length):
	"""Current stock balance per item+warehouse, split into project vs contractor stores
	using each Contractor Assignment's own contractor_warehouse as the dividing line."""
	contractor_warehouses = {w for w in frappe.get_all("CMR Contractor Assignment", pluck="contractor_warehouse") if w}
	rows = frappe.get_all(
		"Bin", fields=["item_code", "warehouse", "actual_qty", "stock_uom"],
		filters={"actual_qty": [">", 0]}, order_by="actual_qty desc", limit_page_length=100000,
	)
	rows = [row for row in rows if (row.warehouse in contractor_warehouses) == (report_type == "contractor-stock")]
	search = (search or "").strip().lower()
	if search:
		rows = [row for row in rows if search in (row.item_code or "").lower() or search in (row.warehouse or "").lower()]
	item_names = {}
	if rows:
		item_names = {
			item.name: item.item_name
			for item in frappe.get_all("Item", fields=["name", "item_name"], filters={"name": ["in", list({row.item_code for row in rows})]})
		}
	for row in rows:
		row["item_name"] = item_names.get(row.item_code, "")
	total = len(rows)
	start = max(int(start or 0), 0)
	page_length = min(max(int(page_length or 50), 1), 200)
	return {"records": rows[start : start + page_length], "total": total}

@frappe.whitelist()
def get_entry_document(entry_type, record_name):
	_check_entry_user()
	_check_entry_edit_site()
	if entry_type not in ENTRY_DOCTYPES:
		frappe.throw("Unsupported CMR entry type")
	doc = frappe.get_doc(ENTRY_DOCTYPES[entry_type], record_name)
	doc.check_permission("read")
	_validate_entry_document(entry_type, doc)
	payload = _entry_payload(entry_type, doc)
	payload["_document"] = _document_info(doc)
	if entry_type == "material-inward" and not cint(doc.get("is_return")) and doc.docstatus == 1:
		payload["_purchase_returns"] = _purchase_return_summary(doc)
	return payload




def _purchase_return_source(purchase_receipt):
	doc = frappe.get_doc("Purchase Receipt", purchase_receipt)
	doc.check_permission("read")
	if doc.docstatus != 1 or cint(doc.is_return):
		frappe.throw("Return Material is available only for a Submitted Material Inward / Purchase Receipt")
	if not doc.get("custom_cmr_site"):
		frappe.throw("Selected Purchase Receipt is not a CMR Material Inward")
	return doc


def _make_native_purchase_return(purchase_receipt):
	from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_return

	return make_purchase_return(purchase_receipt)


def _return_item_rows(source, mapped_return, selected=None):
	selected = selected or {}
	source_rows = {row.name: row for row in source.items}
	rows = []
	for mapped in mapped_return.items:
		source_row = source_rows.get(mapped.purchase_receipt_item)
		if not source_row:
			continue
		available_qty = abs(flt(mapped.qty, 6))
		received_qty = flt(source_row.qty, 6)
		rows.append({
			"source_item": source_row.name,
			"item_code": source_row.item_code,
			"item_name": source_row.item_name,
			"uom": source_row.uom,
			"rate": flt(source_row.rate, 6),
			"warehouse": source_row.warehouse or source.set_warehouse,
			"received_qty": received_qty,
			"already_returned_qty": max(flt(received_qty - available_qty, 6), 0),
			"available_qty": available_qty,
			"return_qty": flt(selected.get(source_row.name), 6),
		})
	return rows


def _purchase_return_summary(source):
	returns = frappe.get_list(
		"Purchase Receipt",
		fields=["name", "posting_date", "docstatus", "status", "total_qty", "grand_total"],
		filters={"is_return": 1, "return_against": source.name},
		order_by="creation desc",
		limit_page_length=200,
	)
	mapped = _make_native_purchase_return(source.name)
	rows = _return_item_rows(source, mapped)
	submitted_returns = [row for row in returns if row.docstatus == 1]
	return {
		"returns": returns,
		"returned_qty": flt(sum(row["already_returned_qty"] for row in rows), 6),
		"available_qty": flt(sum(row["available_qty"] for row in rows), 6),
		"status": "Fully Returned" if rows and not any(row["available_qty"] > 0 for row in rows) else "Partly Returned" if submitted_returns else "Return Draft" if returns else "Not Returned",
	}


def _purchase_return_payload(source, return_doc=None):
	mapped = _make_native_purchase_return(source.name)
	selected = {}
	if return_doc:
		selected = {row.purchase_receipt_item: abs(flt(row.qty, 6)) for row in return_doc.items}
	rows = _return_item_rows(source, mapped, selected)
	taxes = [{
		"description": row.description or row.account_head,
		"charge_type": row.charge_type,
		"rate": flt(row.rate, 6),
		"tax_amount": abs(flt(row.tax_amount, 6)),
	} for row in (return_doc.taxes if return_doc else mapped.taxes)]
	doc = return_doc or mapped
	return {
		"source_name": source.name,
		"record_name": return_doc.name if return_doc else "",
		"posting_date": doc.posting_date,
		"supplier": source.supplier,
		"company": source.company,
		"project": source.get("project"),
		"site": source.get("custom_cmr_site"),
		"warehouse": source.set_warehouse or next((row.warehouse for row in source.items if row.warehouse), ""),
		"supplier_delivery_note": source.supplier_delivery_note,
		"items": rows,
		"taxes": taxes,
		"remarks": doc.remarks,
		"_document": _document_info(return_doc) if return_doc else None,
	}


@frappe.whitelist()
def get_purchase_return_preview(purchase_receipt):
	_check_entry_user()
	_check_entry_edit_site()
	return _purchase_return_payload(_purchase_return_source(purchase_receipt))


@frappe.whitelist()
def get_purchase_return_document(record_name):
	_check_entry_user()
	_check_entry_edit_site()
	doc = frappe.get_doc("Purchase Receipt", record_name)
	doc.check_permission("read")
	if not cint(doc.is_return) or not doc.return_against:
		frappe.throw("Selected document is not a Purchase Receipt Return")
	source = _purchase_return_source(doc.return_against)
	return _purchase_return_payload(source, doc)


def _clean_child_values(row):
	values = row.as_dict()
	for key in ("name", "parent", "parenttype", "parentfield", "idx", "doctype", "creation", "modified", "owner", "modified_by", "docstatus"):
		values.pop(key, None)
	return values


@frappe.whitelist()
def save_purchase_return(purchase_receipt, payload, action="draft", record_name=""):
	_check_entry_user()
	_check_entry_edit_site()
	data = json.loads(payload) if isinstance(payload, str) else (payload or {})
	source = _purchase_return_source(purchase_receipt)
	mapped = _make_native_purchase_return(source.name)
	mapped_items = list(mapped.items)
	available = {row.purchase_receipt_item: abs(flt(row.qty, 6)) for row in mapped_items}
	requested = {}
	for row in data.get("items") or []:
		qty = flt(row.get("return_qty"), 6)
		if qty <= 0:
			continue
		source_item = row.get("source_item")
		if source_item not in available:
			frappe.throw("A selected return item does not belong to the original Purchase Receipt")
		if qty > available[source_item] + 0.000001:
			frappe.throw(f"Return Qty for {row.get('item_code') or source_item} cannot exceed Available Qty {available[source_item]}")
		requested[source_item] = qty
	if not requested:
		frappe.throw("Enter Return Qty for at least one item")

	if record_name:
		doc = frappe.get_doc("Purchase Receipt", record_name)
		doc.check_permission("write")
		if doc.docstatus != 0 or not cint(doc.is_return) or doc.return_against != source.name:
			frappe.throw("Only a Draft Purchase Return against this Material Inward can be edited")
	else:
		_require_permission(source, "create", check_document=False)
		doc = mapped

	doc.posting_date = getdate(data.get("posting_date") or doc.posting_date)
	doc.remarks = data.get("remarks")
	doc.set("items", [])
	for mapped_row in mapped_items:
		qty = requested.get(mapped_row.purchase_receipt_item)
		if not qty:
			continue
		values = _clean_child_values(mapped_row)
		values["qty"] = -qty
		values["received_qty"] = -qty
		values["stock_qty"] = -flt(qty * flt(mapped_row.conversion_factor or 1), 6)
		values["amount"] = -flt(qty * flt(mapped_row.rate), 6)
		values["base_amount"] = -flt(qty * flt(mapped_row.base_rate or mapped_row.rate), 6)
		doc.append("items", values)

	if record_name:
		doc.set("taxes", [])
		for tax in mapped.taxes:
			doc.append("taxes", _clean_child_values(tax))
	doc.run_method("calculate_taxes_and_totals")
	if record_name:
		doc.save()
	else:
		doc.insert()
	if action == "submit":
		_require_permission(doc, "submit")
		doc.submit()
	elif action != "draft":
		frappe.throw("Unsupported Purchase Return action")
	return _purchase_return_payload(source, doc)

@frappe.whitelist()
def run_entry_action(entry_type, record_name, action):
	"""Run the standard ERP document lifecycle without bypassing permissions or validations."""
	_check_entry_user()
	_check_entry_edit_site()
	if entry_type not in ENTRY_DOCTYPES:
		frappe.throw("Unsupported CMR entry type")

	doc = frappe.get_doc(ENTRY_DOCTYPES[entry_type], record_name)
	doc.check_permission("read")
	_validate_entry_document(entry_type, doc)
	action = (action or "").strip().lower()

	if action == "delete":
		if doc.docstatus != 0:
			frappe.throw("Only Draft documents can be deleted")
		_require_permission(doc, "delete")
		frappe.delete_doc(doc.doctype, doc.name)
		return {"name": record_name, "doctype": doc.doctype, "deleted": True}

	if action == "cancel":
		if doc.docstatus != 1:
			frappe.throw("Only Submitted documents can be cancelled")
		_require_permission(doc, "cancel")
		doc.cancel()
	elif action == "duplicate":
		_require_permission(doc, "create", check_document=False)
		duplicate = frappe.copy_doc(doc)
		duplicate.name = None
		duplicate.docstatus = 0
		duplicate.amended_from = None
		duplicate.insert()
		doc = duplicate
	elif action == "amend":
		if doc.docstatus != 2:
			frappe.throw("Only Cancelled documents can be amended")
		_require_permission(doc, "create", check_document=False)
		amended = frappe.copy_doc(doc)
		amended.name = None
		amended.docstatus = 0
		amended.amended_from = doc.name
		amended.insert()
		doc = amended
	elif action in ("close", "reopen"):
		if doc.doctype != "Purchase Receipt" or doc.docstatus != 1:
			frappe.throw("This status action is available only for Submitted Purchase Receipts")
		_require_permission(doc, "submit")
		from erpnext.stock.doctype.purchase_receipt.purchase_receipt import update_purchase_receipt_status

		update_purchase_receipt_status(doc.name, "Closed" if action == "close" else "Submitted")
		doc.reload()
	else:
		frappe.throw("Unsupported document action")

	return _document_info(doc)


@frappe.whitelist()
def save_entry(entry_type, payload, action="draft", record_name=""):
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
	if entry_type == "valves" and action == "submit" and frappe.local.site == ENTRY_EDIT_SITE:
		_validate_valve_submit_gps(data)
	if record_name:
		doc = _update_entry(entry_type, record_name, data, builders[entry_type])
	else:
		doc = builders[entry_type](data)
		doc.insert()

	if action == "submit":
		if frappe.local.site == ENTRY_EDIT_SITE or entry_type != "pipe-laying":
			doc.submit()
		else:
			doc = apply_workflow(doc, "Send for Approval")

	return {
		"name": doc.name,
		"doctype": doc.doctype,
		"docstatus": doc.docstatus,
		"status": doc.get("status"),
	}


def _validate_valve_submit_gps(data):
	if data.get("gps_latitude") in (None, "") or data.get("gps_longitude") in (None, ""):
		frappe.throw("Please capture GPS location before submitting.")
	latitude = flt(data.get("gps_latitude"))
	longitude = flt(data.get("gps_longitude"))
	if not -90 <= latitude <= 90:
		frappe.throw("GPS Latitude must be between -90 and 90")
	if not -180 <= longitude <= 180:
		frappe.throw("GPS Longitude must be between -180 and 180")


def _check_entry_user():
	if frappe.session.user == "Guest":
		frappe.throw("Please sign in to use CMR entry forms", frappe.PermissionError)


def _check_entry_edit_site():
	if frappe.local.site != ENTRY_EDIT_SITE:
		frappe.throw("CMR portal entry editing is enabled only on the Raisoni site", frappe.PermissionError)


def _validate_entry_document(entry_type, doc):
	if doc.doctype != ENTRY_DOCTYPES[entry_type]:
		frappe.throw("Entry document type does not match")
	expected_stock_types = {
		"material-issue": "CMR Contractor Issue",
		"material-return": "CMR Contractor Return",
	}
	if entry_type in expected_stock_types and doc.stock_entry_type != expected_stock_types[entry_type]:
		frappe.throw("Stock Entry does not belong to this CMR transaction type")


def _require_permission(doc, permission_type, check_document=True):
	allowed = frappe.has_permission(
		doc.doctype,
		permission_type,
		doc=doc if check_document else None,
	)
	if not allowed:
		frappe.throw(
			f"You do not have permission to {permission_type} this {doc.doctype}",
			frappe.PermissionError,
		)


def _document_info(doc):
	return {
		"name": doc.name,
		"doctype": doc.doctype,
		"docstatus": doc.docstatus,
		"status": doc.get("status") or ("Draft" if doc.docstatus == 0 else "Submitted" if doc.docstatus == 1 else "Cancelled"),
		"owner": doc.owner,
		"modified": doc.modified,
		"can_write": frappe.has_permission(doc.doctype, "write", doc=doc),
		"can_submit": frappe.has_permission(doc.doctype, "submit", doc=doc),
		"can_cancel": frappe.has_permission(doc.doctype, "cancel", doc=doc),
		"can_delete": frappe.has_permission(doc.doctype, "delete", doc=doc),
		"can_create": frappe.has_permission(doc.doctype, "create"),
		"amended_from": doc.get("amended_from"),
		"is_return": doc.get("is_return") or 0,
		"return_against": doc.get("return_against"),
		"per_billed": flt(doc.get("per_billed")),
	}


def _update_entry(entry_type, record_name, data, builder):
	_check_entry_edit_site()
	source = builder(data)
	doc = frappe.get_doc(source.doctype, record_name)
	doc.check_permission("write")
	_validate_entry_document(entry_type, doc)
	if doc.docstatus != 0:
		frappe.throw("Only Draft entries can be edited in the CMR portal")

	field_map = {
		"material-inward": (
			"company", "supplier", "posting_date", "project", "set_warehouse", "supplier_delivery_note", "remarks",
			"custom_cmr_site", "custom_cmr_mrn_no", "custom_cmr_po_number", "custom_cmr_vehicle_type", "custom_cmr_vehicle_no",
			"custom_cmr_transporter_name", "custom_cmr_transport_cost", "custom_cmr_driver_name", "custom_cmr_driver_mobile",
			"custom_cmr_lr_no", "custom_cmr_invoice_no", "custom_cmr_invoice_date", "custom_cmr_invoice_status",
			"custom_cmr_invoice_attachment", "custom_cmr_test_report_attachment", "custom_cmr_bilty_attachment", "taxes_and_charges",
		),
		"material-issue": (
			"stock_entry_type", "purpose", "company", "posting_date", "project", "from_warehouse", "to_warehouse",
			"source_type", "source_reference", "remarks", "custom_cmr_site", "custom_cmr_contractor_assignment", "custom_cmr_transfer_context",
			"custom_cmr_receiver",
		),
		"material-return": (
			"stock_entry_type", "purpose", "company", "posting_date", "project", "from_warehouse", "to_warehouse",
			"remarks", "custom_cmr_site", "custom_cmr_contractor_assignment", "custom_cmr_transfer_context",
			"custom_cmr_receiver",
		),
		"pipe-laying": (
			"company", "project", "site", "zone", "village", "laying_date", "type_of_work", "laying_mode",
			"trench_method", "section_incharge", "restoration_required", "end_cap", "remarks",
			"contractor_assignment", "contractor_warehouse", "pipe_width",
		),
		"valves": (
			"company", "project", "site", "zone", "village", "installation_date", "pipe_measurement", "pipe_no",
			"valve_item", "uom", "moc", "pressure_rating", "diameter", "current_stock", "chamber_size",
			"specific_location", "gps_latitude", "gps_longitude", "gps_accuracy", "total_fitting_qty", "remarks",
			"quantity", "contractor_assignment", "contractor_warehouse",
		),
		"restoration": (
			"company", "project", "site", "zone", "village", "restoration_date", "pipe_measurement", "pipe_no",
			"restoration_type", "remarks", "contractor_assignment", "pipe_length", "pipe_width", "dismantling_length",
			"dismantling_depth", "dismantling_quantity", "m15_length", "m15_depth", "m15_quantity", "m20_length",
			"m20_depth", "m20_quantity", "m30_length", "m30_depth", "m30_quantity", "total_concrete_quantity", "gps_latitude_from",
			"gps_longitude_from", "gps_latitude_to", "gps_longitude_to",
		),
	}
	table_map = {
		"material-inward": ("items", "custom_cmr_quantity_breakup"),
		"material-issue": ("items",),
		"material-return": ("items",),
		"pipe-laying": ("segments", "excavation_details", "refill_details", "fittings"),
		"valves": ("fittings",),
		"restoration": (),
	}
	for field in field_map[entry_type]:
		if doc.meta.has_field(field):
			doc.set(field, source.get(field))
	for table in table_map[entry_type]:
		doc.set(table, [])
		for row in source.get(table) or []:
			values = row.as_dict()
			for key in ("name", "parent", "parenttype", "parentfield", "idx", "doctype", "creation", "modified", "owner", "modified_by"):
				values.pop(key, None)
			doc.append(table, values)
	doc.save()
	return doc


def _row_values(rows, fields):
	return [{field: row.get(field) for field in fields} for row in (rows or [])]


def _entry_payload(entry_type, doc):
	if entry_type == "material-inward":
		warehouse = doc.set_warehouse or (doc.items[0].warehouse if doc.items else "")
		return {
			"posting_date": doc.posting_date,
			"company": doc.company,
			"project": doc.get("project"),
			"supplier": doc.supplier,
			"site": doc.custom_cmr_site,
			"warehouse": warehouse,
			"supplier_delivery_note": doc.supplier_delivery_note,
			"mrn_no": doc.custom_cmr_mrn_no,
			"po_number": doc.get("custom_cmr_po_number") or next((row.purchase_order for row in doc.items if row.purchase_order), ""),
			"taxes_and_charges": doc.taxes_and_charges,
			"vehicle_type": doc.custom_cmr_vehicle_type or "Truck",
			"vehicle_no": doc.get("custom_cmr_vehicle_no"),
			"transporter_name": doc.get("custom_cmr_transporter_name"),
			"transport_cost": flt(doc.custom_cmr_transport_cost),
			"driver_name": doc.custom_cmr_driver_name,
			"driver_mobile": doc.custom_cmr_driver_mobile,
			"lr_no": doc.custom_cmr_lr_no,
			"invoice_no": doc.get("custom_cmr_invoice_no"),
			"invoice_date": doc.get("custom_cmr_invoice_date"),
			"invoice_status": doc.custom_cmr_invoice_status or "Pending",
			"invoice_attachment": doc.get("custom_cmr_invoice_attachment"),
			"test_report_attachment": doc.get("custom_cmr_test_report_attachment"),
			"bilty_attachment": doc.get("custom_cmr_bilty_attachment"),
			"remarks": doc.remarks,
			"items": [{
				"item_code": row.item_code,
				"qty": flt(row.qty),
				"rate": flt(row.rate),
				"uom": row.uom,
				"material_type": row.get("custom_cmr_material_type") or "Pipe",
				"moc": row.get("custom_cmr_moc"),
				"pressure_rating": row.get("custom_cmr_pressure_rating"),
				"diameter": flt(row.get("custom_cmr_diameter")),
				"consumable_type": row.get("custom_cmr_consumable_type") or "Consumable",
				"purchase_order": row.purchase_order,
				"purchase_order_item": row.purchase_order_item,
			} for row in doc.items],
			"quantity_breakup": _row_values(doc.get("custom_cmr_quantity_breakup") or [], ("item_code", "pipe_or_roll", "nos", "length", "total_length")),
		}
	if entry_type in ("material-issue", "material-return"):
		source_warehouse = doc.from_warehouse or (doc.items[0].s_warehouse if doc.items else "")
		target_warehouse = doc.to_warehouse or (doc.items[0].t_warehouse if doc.items else "")
		return {
			"posting_date": doc.posting_date,
			"material_inward": doc.get("source_reference") if entry_type == "material-issue" else "",
			"company": doc.company,
			"project": doc.project,
			"site": doc.custom_cmr_site,
			"contractor_assignment": doc.custom_cmr_contractor_assignment,
			"source_warehouse": source_warehouse,
			"target_warehouse": target_warehouse,
			"receiver": doc.custom_cmr_receiver,
			"remarks": doc.remarks,
			"items": [_transfer_item_payload(row, source_warehouse, target_warehouse) for row in doc.items],
		}
	if entry_type == "pipe-laying":
		fields = (
			"laying_date", "company", "project", "site", "zone", "village", "type_of_work", "laying_mode",
			"trench_method", "section_incharge", "contractor_assignment", "pipe_width", "restoration_required",
			"end_cap", "remarks",
		)
		payload = {field: doc.get(field) for field in fields}
		payload["segments"] = _row_values(doc.segments, ("pipe_no", "pipe_item", "start_node", "end_node", "chainage_from", "chainage_to", "chainage_length", "actual_length", "diameter", "moc", "pressure_rating"))
		payload["excavation_details"] = _row_values(doc.excavation_details, ("excavation_type", "length", "width", "calculated_depth", "actual_depth", "calculated_qty", "actual_qty"))
		payload["refill_details"] = _row_values(doc.refill_details, ("material_type", "length", "width", "depth", "quantity"))
		payload["fittings"] = _row_values(doc.fittings, ("item_code", "quantity", "uom", "current_stock", "moc", "pressure_rating", "diameter"))
		return payload
	if entry_type == "valves":
		fields = (
			"installation_date", "company", "project", "site", "zone", "village", "pipe_measurement", "pipe_no",
			"contractor_assignment", "valve_item", "quantity", "uom", "moc", "pressure_rating", "diameter",
			"current_stock", "chamber_size", "specific_location", "gps_latitude", "gps_longitude", "gps_accuracy",
			"total_fitting_qty", "remarks",
		)
		payload = {field: doc.get(field) for field in fields}
		payload["fittings"] = _row_values(doc.fittings, ("item_code", "quantity", "uom", "current_stock", "moc", "pressure_rating", "diameter"))
		return payload
	fields = (
		"restoration_date", "company", "project", "site", "zone", "village", "pipe_measurement", "pipe_no",
		"contractor_assignment", "pipe_length", "pipe_width", "restoration_type", "dismantling_length", "dismantling_depth",
		"dismantling_quantity", "m15_length", "m15_depth", "m15_quantity", "m20_length", "m20_depth", "m20_quantity",
		"m30_length", "m30_depth", "m30_quantity", "total_concrete_quantity", "gps_latitude_from", "gps_longitude_from",
		"gps_latitude_to", "gps_longitude_to", "remarks",
	)
	return {field: doc.get(field) for field in fields}


def _item_catalog(limit=1000):
	"""Return stock items enriched from native Item Variant Attribute rows."""
	item_meta = frappe.get_meta("Item")
	custom_fields = [
		field for field in ("custom_cmr_material_type", "custom_cmr_moc", "custom_cmr_pressure_rating", "custom_cmr_diameter")
		if item_meta.has_field(field)
	]
	rows = _list(
		"Item",
		["name", "item_code", "item_name", "stock_uom", "item_group", *custom_fields],
		{"disabled": 0, "is_stock_item": 1},
		limit,
	)
	by_item = {row.item_code: row for row in rows}
	for row in rows:
		row.update({
			"material_type": row.get("custom_cmr_material_type") or row.item_group,
			"moc": row.get("custom_cmr_moc") or "",
			"pressure_rating": row.get("custom_cmr_pressure_rating") or "",
			"diameter": row.get("custom_cmr_diameter") or "",
		})
	if not by_item:
		return rows

	attribute_map = {
		"material type": "material_type",
		"item type": "material_type",
		"moc": "moc",
		"material of construction": "moc",
		"class": "pressure_rating",
		"specification": "pressure_rating",
		"pressure rating": "pressure_rating",
		"size": "diameter",
		"diameter": "diameter",
		"dia": "diameter",
	}
	for value in frappe.get_all(
		"Item Variant Attribute",
		fields=["parent", "attribute", "attribute_value"],
		filters={"parent": ["in", list(by_item)]},
		limit_page_length=10000,
	):
		target = attribute_map.get((value.attribute or "").strip().lower())
		if target and value.parent in by_item:
			by_item[value.parent][target] = value.attribute_value
	return rows


def _item_attribute_options():
	"""Expose ERPNext Item Attribute values to every new-UI material selector."""
	aliases = {
		"material type": "material_type", "item type": "material_type",
		"moc": "moc", "material of construction": "moc",
		"class": "pressure_rating", "specification": "pressure_rating", "pressure rating": "pressure_rating",
		"size": "diameter", "diameter": "diameter", "dia": "diameter",
	}
	result = {"material_type": [], "moc": [], "pressure_rating": [], "diameter": []}
	for attribute in frappe.get_all("Item Attribute", fields=["name", "attribute_name"], limit_page_length=500):
		target = aliases.get((attribute.attribute_name or attribute.name or "").strip().lower())
		if not target:
			continue
		values = frappe.get_all(
			"Item Attribute Value", fields=["attribute_value"], filters={"parent": attribute.name},
			order_by="idx asc", limit_page_length=1000,
		)
		for row in values:
			value = (row.attribute_value or "").strip()
			if value and value not in result[target]:
				result[target].append(value)
	return result


def _select_field_options():
	"""Read Select options from live DocType metadata instead of duplicating them in Vue."""
	fields = {
		"vehicle_type": ("Purchase Receipt", "custom_cmr_vehicle_type"),
		"invoice_status": ("Purchase Receipt", "custom_cmr_invoice_status"),
		"material_type": ("Purchase Receipt Item", "custom_cmr_material_type"),
		"consumable_type": ("Purchase Receipt Item", "custom_cmr_consumable_type"),
		"pipe_or_roll": ("CMR Material Quantity Breakup", "pipe_or_roll"),
		"type_of_work": ("CMR Pipe Laying Measurement", "type_of_work"),
		"laying_mode": ("CMR Pipe Laying Measurement", "laying_mode"),
		"trench_method": ("CMR Pipe Laying Measurement", "trench_method"),
		"end_cap": ("CMR Pipe Laying Measurement", "end_cap"),
		"excavation_type": ("CMR Excavation Detail", "excavation_type"),
		"refill_material": ("CMR Refill Detail", "material_type"),
		"restoration_type": ("CMR Road Restoration", "restoration_type"),
		"supplier_type": ("Supplier", "supplier_type"),
		"contractor_work_type": ("CMR Contractor Assignment", "work_type"),
		"item_material_type": ("Item", "custom_cmr_material_type"),
		"item_moc": ("Item", "custom_cmr_moc"),
		"item_pressure_rating": ("Item", "custom_cmr_pressure_rating"),
	}
	result = {}
	for key, (doctype, fieldname) in fields.items():
		field = frappe.get_meta(doctype).get_field(fieldname)
		result[key] = [value.strip() for value in ((field.options if field else "") or "").splitlines() if value.strip()]
	return result

def _list(doctype, fields, filters=None, limit=500):
	try:
		return frappe.get_list(doctype, fields=fields, filters=filters or {}, order_by="modified desc", limit_page_length=limit)
	except frappe.PermissionError:
		return []


def _all(doctype, fields, filters=None, limit=500):
	return frappe.get_all(doctype, fields=fields, filters=filters or {}, order_by="modified desc", limit_page_length=limit)


def _hierarchy_options(doctype, fields):
	if frappe.local.site != ENTRY_EDIT_SITE or not frappe.db.exists("DocType", doctype):
		return []
	return _all(doctype, fields, {"enabled": 1})


def _required(data, *fields):
	missing = [field.replace("_", " ").title() for field in fields if not data.get(field)]
	if missing:
		frappe.throw(f"Please fill: {', '.join(missing)}")


def _positive_items(rows):
	items = [row for row in (rows or []) if row.get("item_code") and flt(row.get("qty")) > 0]
	if not items:
		frappe.throw("Add at least one item with a positive quantity")
	return items


def _item_metadata(item_code):
	for item in _item_catalog():
		if item.item_code == item_code:
			return item
	return frappe._dict({
		"material_type": "",
		"moc": "",
		"pressure_rating": "",
		"diameter": "",
	})


def _transfer_item_payload(row, source_warehouse, target_warehouse):
	metadata = _item_metadata(row.item_code)
	return {
		"item_code": row.item_code,
		"qty": flt(row.qty),
		"rate": 0,
		"uom": row.uom,
		"material_type": metadata.material_type,
		"moc": metadata.moc,
		"pressure_rating": metadata.pressure_rating,
		"diameter": metadata.diameter,
		"consumable_type": "Consumable",
		"source_stock": flt(get_stock_balance(row.item_code, source_warehouse), 3) if source_warehouse else 0,
		"target_stock": flt(get_stock_balance(row.item_code, target_warehouse), 3) if target_warehouse else 0,
	}


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
	_required(data, "company", "project", "supplier", "posting_date", "site", "warehouse")
	transport_cost = flt(data.get("transport_cost"))
	if transport_cost < 0:
		frappe.throw("Transport Cost cannot be negative")
	doc = frappe.new_doc("Purchase Receipt")
	doc.company = data["company"]
	doc.project = data["project"]
	doc.supplier = data["supplier"]
	doc.posting_date = getdate(data["posting_date"])
	doc.set_warehouse = data["warehouse"]
	doc.supplier_delivery_note = data.get("supplier_delivery_note")
	doc.remarks = data.get("remarks")
	doc.custom_cmr_site = data["site"]
	if frappe.local.site == ENTRY_EDIT_SITE:
		site_project = frappe.db.get_value("CMR Site", data["site"], "project")
		if not site_project or site_project != data["project"]:
			frappe.throw("Selected Site does not belong to the selected Project")
	doc.custom_cmr_mrn_no = data.get("mrn_no")
	if doc.meta.has_field("custom_cmr_po_number"):
		doc.custom_cmr_po_number = (data.get("po_number") or "").strip()
	doc.custom_cmr_vehicle_type = data.get("vehicle_type")
	doc.custom_cmr_transport_cost = transport_cost
	doc.custom_cmr_driver_name = data.get("driver_name")
	doc.custom_cmr_driver_mobile = data.get("driver_mobile")
	doc.custom_cmr_lr_no = data.get("lr_no")
	doc.custom_cmr_invoice_status = data.get("invoice_status") or "Pending"
	for field, value in {
		"custom_cmr_vehicle_no": data.get("vehicle_no"),
		"custom_cmr_transporter_name": data.get("transporter_name"),
		"custom_cmr_invoice_no": data.get("invoice_no"),
		"custom_cmr_invoice_date": getdate(data.get("invoice_date")) if data.get("invoice_date") else None,
		"custom_cmr_invoice_attachment": data.get("invoice_attachment"),
		"custom_cmr_test_report_attachment": data.get("test_report_attachment"),
		"custom_cmr_bilty_attachment": data.get("bilty_attachment"),
	}.items():
		if doc.meta.has_field(field):
			doc.set(field, value)
	if doc.meta.has_field("source_app"):
		doc.source_app = "CMR Pipe Laying Master"
	for row in _positive_items(data.get("items")):
		values = _item_values(row["item_code"], row["qty"], data["warehouse"], row.get("rate"))
		values.update({
			"purchase_order": row.get("purchase_order"),
			"purchase_order_item": row.get("purchase_order_item"),
			"custom_cmr_material_type": row.get("material_type"),
			"custom_cmr_moc": row.get("moc"),
			"custom_cmr_pressure_rating": row.get("pressure_rating"),
			"custom_cmr_diameter": flt(row.get("diameter")),
			"custom_cmr_consumable_type": row.get("consumable_type"),
		})
		doc.append("items", values)
	_append_purchase_taxes(doc, data.get("taxes_and_charges"))
	if doc.meta.has_field("custom_cmr_quantity_breakup"):
		_set_quantity_breakup(doc, data.get("quantity_breakup"))
	return doc


def _append_purchase_taxes(doc, template_name):
	if not template_name:
		return
	template = frappe.get_doc("Purchase Taxes and Charges Template", template_name)
	template.check_permission("read")
	if template.company and template.company != doc.company:
		frappe.throw("Purchase Tax Template must belong to the selected Company")
	doc.taxes_and_charges = template.name
	for row in template.taxes:
		values = row.as_dict()
		for key in ("name", "parent", "parenttype", "parentfield", "idx", "doctype", "creation", "modified", "owner", "modified_by"):
			values.pop(key, None)
		doc.append("taxes", values)


def _set_quantity_breakup(doc, rows):
	rows = rows or []
	if not rows:
		return
	item_quantities = {row.item_code: flt(row.qty) for row in doc.items}
	totals = defaultdict(float)
	for index, row in enumerate(rows, 1):
		item_code = row.get("item_code")
		nos = flt(row.get("nos"))
		length = flt(row.get("length"))
		if not item_code or item_code not in item_quantities:
			frappe.throw(f"Quantity Breakup row {index}: select an Item present in Material Items")
		if nos <= 0 or length <= 0:
			frappe.throw(f"Quantity Breakup row {index}: Nos and Length must be greater than zero")
		total_length = flt(nos * length, 3)
		totals[item_code] += total_length
		doc.append("custom_cmr_quantity_breakup", {
			"item_code": item_code,
			"pipe_or_roll": row.get("pipe_or_roll"),
			"nos": nos,
			"length": length,
			"total_length": total_length,
		})
	for item_code, total_length in totals.items():
		if abs(flt(item_quantities[item_code], 3) - flt(total_length, 3)) > 0.001:
			frappe.throw(
				f"Quantity Breakup total for {item_code} must equal Material Item quantity "
				f"({flt(item_quantities[item_code], 3)})"
			)


def _build_stock_entry(data, is_return):
	_required(data, "company", "posting_date", "site", "source_warehouse", "target_warehouse")
	if data["source_warehouse"] == data["target_warehouse"]:
		frappe.throw("From Warehouse and To Warehouse cannot be the same. Select a different Contractor Warehouse in Contractor master.")
	source_receipt = None
	allowed_receipt_items = set()
	if not is_return and data.get("material_inward"):
		source_receipt = _submitted_material_inward(data["material_inward"])
		if source_receipt.company != data["company"]:
			frappe.throw("Selected Material Inward does not belong to the selected Company")
		if source_receipt.project and source_receipt.project != data.get("project"):
			frappe.throw("Selected Material Inward does not belong to the selected Project")
		if source_receipt.custom_cmr_site != data["site"]:
			frappe.throw("Selected Material Inward does not belong to the selected Site")
		if _material_inward_warehouse(source_receipt) != data["source_warehouse"]:
			frappe.throw("From Warehouse must match the selected Material Inward Receiving Warehouse")
		allowed_receipt_items = {row.item_code for row in source_receipt.items if row.item_code}
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
	doc.custom_cmr_receiver = data.get("receiver")
	if source_receipt:
		if doc.meta.has_field("source_type"):
			doc.source_type = source_receipt.doctype
		if doc.meta.has_field("source_reference"):
			doc.source_reference = source_receipt.name
	for row in _positive_items(data.get("items")):
		if source_receipt and row["item_code"] not in allowed_receipt_items:
			frappe.throw(f"Item {row['item_code']} is not present in selected Material Inward {source_receipt.name}")
		available_stock = flt(get_stock_balance(row["item_code"], data["source_warehouse"]), 3)
		if is_return and flt(row["qty"], 3) > available_stock:
			frappe.throw(
				f"Return quantity for {row['item_code']} ({flt(row['qty'], 3)}) cannot exceed "
				f"available contractor stock ({available_stock})"
			)
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
	strict_calculations = frappe.local.site == ENTRY_EDIT_SITE
	for row in data.get("segments") or []:
		if strict_calculations or (row.get("pipe_item") and flt(row.get("actual_length")) > 0):
			doc.append("segments", row)
	for row in data.get("excavation_details") or []:
		if row.get("excavation_type") and (strict_calculations or flt(row.get("length")) > 0):
			doc.append("excavation_details", row)
	for row in data.get("refill_details") or []:
		if row.get("material_type") and (strict_calculations or flt(row.get("depth")) > 0):
			doc.append("refill_details", row)
	for row in data.get("fittings") or []:
		if strict_calculations or (row.get("item_code") and flt(row.get("quantity")) > 0):
			doc.append("fittings", row)
	return doc


def _build_valve_installation(data):
	_required(data, "company", "project", "site", "zone", "village", "installation_date", "pipe_measurement", "pipe_no", "valve_item", "quantity", "chamber_size")
	assignment = _assignment(data)
	doc = frappe.new_doc("CMR Valve Installation")
	for field in ("company", "project", "site", "zone", "village", "installation_date", "pipe_measurement", "pipe_no", "valve_item", "uom", "moc", "pressure_rating", "diameter", "current_stock", "chamber_size", "specific_location", "gps_latitude", "gps_longitude", "gps_accuracy", "total_fitting_qty", "remarks"):
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
	for field in ("pipe_length", "pipe_width", "dismantling_length", "dismantling_depth", "dismantling_quantity", "m15_length", "m15_depth", "m15_quantity", "m20_length", "m20_depth", "m20_quantity", "m30_length", "m30_depth", "m30_quantity", "total_concrete_quantity", "gps_latitude_from", "gps_longitude_from", "gps_latitude_to", "gps_longitude_to"):
		doc.set(field, flt(data.get(field)))
	return doc
