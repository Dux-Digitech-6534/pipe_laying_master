from collections import defaultdict

import frappe
from frappe.utils import flt
from erpnext.stock.utils import get_stock_balance


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
ATTRIBUTE_FIELD_MAP = {
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


def get_item_operational_details(item_code, warehouse=None):
	"""Return native Item/UOM, variant attributes and live ERPNext stock balance."""
	item = frappe.get_cached_doc("Item", item_code)
	values = frappe._dict({
		"uom": item.stock_uom,
		"material_type": (
			item.get("custom_cmr_material_type")
			if item.meta.has_field("custom_cmr_material_type")
			else ""
		) or item.item_group,
		"moc": item.get("custom_cmr_moc") if item.meta.has_field("custom_cmr_moc") else "",
		"pressure_rating": item.get("custom_cmr_pressure_rating") if item.meta.has_field("custom_cmr_pressure_rating") else "",
		"diameter": flt(item.get("custom_cmr_diameter")) if item.meta.has_field("custom_cmr_diameter") else 0,
		"current_stock": flt(get_stock_balance(item_code, warehouse), 3) if warehouse else 0,
	})
	for row in frappe.get_all(
		"Item Variant Attribute",
		fields=["attribute", "attribute_value"],
		filters={"parent": item_code},
		limit_page_length=100,
	):
		target = ATTRIBUTE_FIELD_MAP.get((row.attribute or "").strip().lower())
		if target:
			values[target] = flt(row.attribute_value) if target == "diameter" else row.attribute_value
	return values


def validate_execution_item_type(item_code, expected_type, material_type=None):
	"""Reject execution items that do not match the existing Item material classification."""
	actual_type = material_type
	if actual_type is None:
		actual_type = get_item_operational_details(item_code).material_type
	if (actual_type or "").strip().casefold() != (expected_type or "").strip().casefold():
		frappe.throw(
			frappe._("Selected item {0} is not a {1} item.").format(
				frappe.bold(item_code), frappe.bold(expected_type)
			)
		)
	return actual_type
