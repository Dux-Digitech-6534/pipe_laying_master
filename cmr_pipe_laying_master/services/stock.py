from collections import defaultdict

import frappe
from frappe.utils import flt


ENTRY_TYPES = {
	"CMR Pipe Laying Measurement": ("CMR Pipe Consumption", "Pipe Consumption"),
	"CMR Valve Installation": ("CMR Valve Consumption", "Valve Consumption"),
}


def create_execution_consumption(document):
	"""Create and submit the standard ERPNext Material Issue that owns stock impact."""
	warehouse = document.contractor_warehouse
	if not warehouse:
		frappe.throw("Contractor Warehouse is required before submission")

	quantities = defaultdict(float)
	if document.doctype == "CMR Pipe Laying Measurement":
		for row in document.segments:
			quantities[row.pipe_item] += flt(row.actual_length)
		for row in document.fittings:
			quantities[row.item_code] += flt(row.quantity)
	elif document.doctype == "CMR Valve Installation":
		quantities[document.valve_item] += flt(document.quantity)
		for row in document.fittings:
			quantities[row.item_code] += flt(row.quantity)

	quantities = {item: qty for item, qty in quantities.items() if item and qty > 0}
	if not quantities:
		frappe.throw("At least one stock item with a positive quantity is required")

	entry_type, context = ENTRY_TYPES[document.doctype]
	entry = frappe.new_doc("Stock Entry")
	entry.stock_entry_type = entry_type
	entry.purpose = "Material Issue"
	entry.company = document.company
	entry.project = document.project
	entry.from_warehouse = warehouse
	entry.source_type = document.doctype
	entry.source_reference = document.name
	entry.remarks = f"CMR execution consumption against {document.doctype} {document.name}"
	if entry.meta.has_field("custom_cmr_site"):
		entry.custom_cmr_site = document.site
		entry.custom_cmr_contractor_assignment = document.contractor_assignment
		entry.custom_cmr_transfer_context = context

	for item_code, quantity in quantities.items():
		item = frappe.get_cached_doc("Item", item_code)
		entry.append("items", {
			"item_code": item_code,
			"qty": quantity,
			"s_warehouse": warehouse,
			"uom": item.stock_uom,
			"stock_uom": item.stock_uom,
			"conversion_factor": 1,
		})

	entry.insert()
	entry.submit()
	return entry.name


def cancel_linked_stock_entry(stock_entry):
	if not stock_entry or not frappe.db.exists("Stock Entry", stock_entry):
		return
	entry = frappe.get_doc("Stock Entry", stock_entry)
	if entry.docstatus == 1:
		entry.cancel()
