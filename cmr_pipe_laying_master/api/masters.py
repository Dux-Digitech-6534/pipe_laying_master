import json

import frappe


ALLOWED_ROLES = ("System Manager", "CMR Pipe Admin", "CMR Master Manager")


@frappe.whitelist()
def get_master_options():
	_check_access()
	return {
		"companies": _list("Company", ["name"]),
		"projects": _list("Project", ["name", "project_name", "company"]),
		"sites": _list("CMR Site", ["name", "site_name", "company", "project"]),
		"suppliers": _list("Supplier", ["name", "supplier_name"]),
		"warehouses": _list("Warehouse", ["name", "warehouse_name", "company"], {"is_group": 0}),
		"parent_warehouses": _list("Warehouse", ["name", "warehouse_name", "company"], {"is_group": 1}),
		"item_groups": _list("Item Group", ["name", "item_group_name"], {"is_group": 0}),
		"uoms": _list("UOM", ["name", "uom_name"]),
		"supplier_groups": _list("Supplier Group", ["name", "supplier_group_name"], {"is_group": 0}),
		"users": _list("User", ["name", "full_name"], {"enabled": 1}),
	}


@frappe.whitelist()
def save_master(master_type, payload):
	_check_access()
	data = json.loads(payload) if isinstance(payload, str) else payload
	builders = {
		"master-project": _project,
		"master-site": _site,
		"master-material": _item,
		"master-contractor": _contractor,
		"master-supplier": _supplier,
		"master-store": _warehouse,
		"master-attributes": _attribute,
	}
	if master_type not in builders:
		frappe.throw("Unsupported CMR master type")
	doc = builders[master_type](data)
	doc.insert(ignore_permissions=True)
	return {"name": doc.name, "doctype": doc.doctype}


@frappe.whitelist()
def get_master_records(master_type, search="", start=0, page_length=50):
	_check_access()
	configs = {
		"master-project": ("Project", ["name", "project_name"], ["name", "project_name"]),
		"master-site": ("CMR Site", ["name", "site_name"], ["name", "site_name"]),
		"master-material": ("Item", ["name", "item_code", "item_name", "item_group", "stock_uom", "disabled"], ["name", "item_code", "item_name", "item_group"]),
	}
	if master_type not in configs:
		frappe.throw("Unsupported master list")
	doctype, fields, search_fields = configs[master_type]
	search = (search or "").strip()
	filters = [[doctype, field, "like", f"%{search}%"] for field in search_fields] if search else []
	records = frappe.get_all(
		doctype,
		fields=fields,
		or_filters=filters,
		order_by="modified desc",
		start=max(int(start or 0), 0),
		page_length=min(max(int(page_length or 50), 1), 200),
	)
	if search:
		count = len(frappe.get_all(doctype, fields=["name"], or_filters=filters, limit_page_length=0))
	else:
		count = frappe.db.count(doctype)
	return {"records": records, "total": count}


def _check_access():
	if frappe.session.user == "Guest" or not set(frappe.get_roles()).intersection(ALLOWED_ROLES):
		frappe.throw("CMR Master Manager role is required", frappe.PermissionError)


def _list(doctype, fields, filters=None):
	return frappe.get_all(doctype, fields=fields, filters=filters or {}, order_by="modified desc", limit_page_length=1000)


def _required(data, *fields):
	missing = [field.replace("_", " ").title() for field in fields if not data.get(field)]
	if missing:
		frappe.throw(f"Please fill: {', '.join(missing)}")


def _default_company():
	return frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company") or frappe.db.get_value("Company")


def _project(data):
	if frappe.local.site != "jewipl.duxdigitech.in":
		return _project_full(data)
	_required(data, "project_name")
	doc = frappe.new_doc("Project")
	doc.project_name = data["project_name"]
	doc.company = _default_company()
	doc.status = "Open"
	doc.is_active = "Yes"
	return doc


def _project_full(data):
	_required(data, "project_name", "company")
	doc = frappe.new_doc("Project")
	doc.project_name = data["project_name"]
	doc.company = data["company"]
	doc.status = "Open"
	doc.is_active = "Yes"
	doc.expected_start_date = data.get("expected_start_date")
	doc.expected_end_date = data.get("expected_end_date")
	doc.notes = data.get("notes")
	return doc


def _site(data):
	if frappe.local.site != "jewipl.duxdigitech.in":
		return _site_full(data)
	_required(data, "site_name")
	doc = frappe.new_doc("CMR Site")
	doc.site_name = data["site_name"]
	doc.status = "Active"
	doc.flags.ignore_mandatory = True
	return doc


def _site_full(data):
	_required(data, "site_name", "company", "project")
	doc = frappe.new_doc("CMR Site")
	for field in ("site_name", "company", "project", "zone", "village", "site_incharge", "default_warehouse", "address"):
		doc.set(field, data.get(field))
	doc.status = "Active"
	return doc


def _item(data):
	_required(data, "item_code", "item_name", "item_group", "stock_uom")
	doc = frappe.new_doc("Item")
	doc.item_code = data["item_code"]
	doc.item_name = data["item_name"]
	doc.item_group = data["item_group"]
	doc.stock_uom = data["stock_uom"]
	doc.is_stock_item = 1
	doc.description = data.get("description") or data["item_name"]
	return doc


def _supplier(data):
	_required(data, "supplier_name", "supplier_group")
	doc = frappe.new_doc("Supplier")
	doc.supplier_name = data["supplier_name"]
	doc.supplier_group = data["supplier_group"]
	doc.supplier_type = data.get("supplier_type") or "Company"
	doc.mobile_no = data.get("mobile_no")
	doc.email_id = data.get("email_id")
	return doc


def _warehouse(data):
	_required(data, "warehouse_name", "company", "parent_warehouse")
	doc = frappe.new_doc("Warehouse")
	doc.warehouse_name = data["warehouse_name"]
	doc.company = data["company"]
	doc.parent_warehouse = data["parent_warehouse"]
	doc.is_group = 0
	return doc


def _contractor(data):
	_required(data, "contractor", "company", "project", "site", "work_type")
	doc = frappe.new_doc("CMR Contractor Assignment")
	for field in ("contractor", "company", "project", "site", "work_type", "contractor_warehouse", "from_date", "to_date"):
		doc.set(field, data.get(field))
	doc.active = 1
	return doc


def _attribute(data):
	_required(data, "attribute_name", "values")
	doc = frappe.new_doc("Item Attribute")
	doc.attribute_name = data["attribute_name"]
	doc.numeric_values = 0
	for value in [part.strip() for part in data["values"].split(",") if part.strip()]:
		doc.append("item_attribute_values", {"attribute_value": value, "abbr": value[:10]})
	return doc
