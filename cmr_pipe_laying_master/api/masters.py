import json

import frappe


SIMPLE_MASTER_SITES = {
	"jewipl.duxdigitech.in",
	"raisonigroup.duxdigitech.in",
}
MASTER_EDIT_SITE = "raisonigroup.duxdigitech.in"
EDITABLE_MASTERS = {
	"master-project": ("Project", ("name", "project_name")),
	"master-site": ("CMR Site", ("name", "site_name", "project")),
	"master-zone": ("CMR Zone", ("name", "zone_name", "project", "site", "enabled")),
	"master-village": ("CMR Village", ("name", "village_name", "project", "site", "zone", "enabled")),
	"master-material": ("Item", ("name", "item_code", "item_name", "item_group", "stock_uom", "is_stock_item", "description", "custom_cmr_material_type", "custom_cmr_moc", "custom_cmr_pressure_rating", "custom_cmr_diameter")),
	"master-contractor": ("CMR Contractor Assignment", ("name", "contractor", "company", "project", "site", "work_type", "contractor_warehouse", "from_date", "to_date", "active")),
	"master-supplier": ("Supplier", ("name", "supplier_name", "supplier_group", "supplier_type", "mobile_no", "email_id")),
	"master-store": ("Warehouse", ("name", "warehouse_name", "company", "parent_warehouse")),
	"master-attributes": ("Item Attribute", ("name", "attribute_name", "numeric_values")),
}


@frappe.whitelist()
def get_master_options():
	_check_signed_in()
	from cmr_pipe_laying_master.api.entries import _item_attribute_options, _select_field_options

	return {
		"companies": _list("Company", ["name"]),
		"projects": _list("Project", ["name", "project_name", "company"]),
		"sites": _list("CMR Site", ["name", "site_name", "company", "project"]),
		"zones": _raisoni_master_list("CMR Zone", ["name", "zone_name", "project", "site", "enabled"]),
		"villages": _raisoni_master_list("CMR Village", ["name", "village_name", "project", "site", "zone", "enabled"]),
		"suppliers": _list("Supplier", ["name", "supplier_name"]),
		"warehouses": _list("Warehouse", ["name", "warehouse_name", "company"], {"is_group": 0}),
		"parent_warehouses": _list("Warehouse", ["name", "warehouse_name", "company"], {"is_group": 1}),
		"item_groups": _list("Item Group", ["name", "item_group_name"], {"is_group": 0}),
		"uoms": _list("UOM", ["name", "uom_name"]),
		"supplier_groups": _list("Supplier Group", ["name", "supplier_group_name"], {"is_group": 0}),
		"users": _list("User", ["name", "full_name"], {"enabled": 1}),
		"item_attributes": _item_attribute_options(),
		"select_options": _select_field_options(),
	}


@frappe.whitelist()
def get_master_document(master_type, record_name):
	_check_signed_in()
	_check_master_edit_site()
	if master_type not in EDITABLE_MASTERS:
		frappe.throw("This CMR master cannot be edited from the portal")
	doctype, fields = EDITABLE_MASTERS[master_type]
	doc = frappe.get_doc(doctype, record_name)
	doc.check_permission("read")
	result = {field: doc.get(field) for field in fields}
	if master_type == "master-attributes":
		result["values"] = ", ".join(row.attribute_value for row in doc.item_attribute_values if row.attribute_value)
	return result


@frappe.whitelist()
def save_master(master_type, payload, record_name=""):
	_check_signed_in()
	data = json.loads(payload) if isinstance(payload, str) else payload
	builders = {
		"master-project": _project,
		"master-site": _site,
		"master-zone": _zone,
		"master-village": _village,
		"master-material": _item,
		"master-contractor": _contractor,
		"master-supplier": _supplier,
		"master-store": _warehouse,
		"master-attributes": _attribute,
	}
	if master_type not in builders:
		frappe.throw("Unsupported CMR master type")
	if record_name:
		return _update_master(master_type, record_name, data)
	doc = builders[master_type](data)
	doc.insert()
	return {"name": doc.name, "doctype": doc.doctype, "action": "created"}


@frappe.whitelist()
def get_master_records(master_type, search="", start=0, page_length=50):
	_check_signed_in()
	configs = {
		"master-project": ("Project", ["name", "project_name"], ["name", "project_name"]),
		"master-site": ("CMR Site", ["name", "site_name", "project"], ["name", "site_name", "project"]),
		"master-zone": ("CMR Zone", ["name", "zone_name", "project", "site", "enabled"], ["name", "zone_name", "project", "site"]),
		"master-village": ("CMR Village", ["name", "village_name", "project", "site", "zone", "enabled"], ["name", "village_name", "project", "site", "zone"]),
		"master-material": ("Item", ["name", "item_code", "item_name", "item_group", "stock_uom", "disabled"], ["name", "item_code", "item_name", "item_group"]),
		"master-contractor": ("CMR Contractor Assignment", ["name", "contractor", "project", "site", "work_type", "active"], ["name", "contractor", "project", "site", "work_type"]),
		"master-supplier": ("Supplier", ["name", "supplier_name", "supplier_group", "supplier_type"], ["name", "supplier_name", "supplier_group", "supplier_type"]),
		"master-store": ("Warehouse", ["name", "warehouse_name", "company", "parent_warehouse"], ["name", "warehouse_name"]),
		"master-attributes": ("Item Attribute", ["name", "attribute_name", "numeric_values"], ["name", "attribute_name"]),
	}
	if master_type not in configs:
		frappe.throw("Unsupported master list")
	if master_type in ("master-zone", "master-village"):
		_check_master_edit_site()
	doctype, fields, search_fields = configs[master_type]
	base_filters = {"is_group": 0} if master_type == "master-store" else {}
	search = (search or "").strip()
	filters = [[doctype, field, "like", f"%{search}%"] for field in search_fields] if search else []
	records = frappe.get_list(
		doctype,
		fields=fields,
		filters=base_filters,
		or_filters=filters,
		order_by="modified desc",
		start=max(int(start or 0), 0),
		page_length=min(max(int(page_length or 50), 1), 200),
	)
	if search:
		count = len(frappe.get_list(doctype, fields=["name"], filters=base_filters, or_filters=filters, limit_page_length=100000))
	else:
		count = len(frappe.get_list(doctype, fields=["name"], filters=base_filters, limit_page_length=100000))
	return {"records": records, "total": count}


def _check_signed_in():
	if frappe.session.user == "Guest":
		frappe.throw("Please sign in to use CMR masters", frappe.PermissionError)


def _check_master_edit_site():
	if frappe.local.site != MASTER_EDIT_SITE:
		frappe.throw("CMR portal editing is enabled only on the Raisoni site", frappe.PermissionError)


def _update_master(master_type, record_name, data):
	_check_master_edit_site()
	if master_type not in EDITABLE_MASTERS:
		frappe.throw("This CMR master cannot be edited from the portal")
	doctype = EDITABLE_MASTERS[master_type][0]
	doc = frappe.get_doc(doctype, record_name)
	doc.check_permission("write")
	if master_type == "master-project":
		_required(data, "project_name")
		doc.project_name = data["project_name"]
	elif master_type == "master-site":
		_required(data, "site_name", "project")
		doc.site_name = data["site_name"]
		doc.project = data["project"]
		doc.company = _project_company(data["project"])
	elif master_type == "master-zone":
		_required(data, "zone_name", "project", "site")
		for field in ("zone_name", "project", "site", "enabled"):
			doc.set(field, data.get(field))
	elif master_type == "master-village":
		_required(data, "village_name", "project", "site", "zone")
		for field in ("village_name", "project", "site", "zone", "enabled"):
			doc.set(field, data.get(field))
	elif master_type == "master-material":
		_required(data, "item_code", "item_name", "item_group", "stock_uom")
		if data["item_code"] != doc.item_code:
			frappe.throw("Item Code cannot be changed after creation")
		for field in ("item_name", "item_group", "stock_uom", "description"):
			doc.set(field, data.get(field))
		doc.is_stock_item = 1 if data.get("is_stock_item", 1) else 0
		_set_item_classification(doc, data)
	elif master_type == "master-contractor":
		_required(data, "contractor", "company", "project", "site", "work_type")
		for field in ("contractor", "company", "project", "site", "work_type", "contractor_warehouse", "from_date", "to_date"):
			doc.set(field, data.get(field))
	elif master_type == "master-supplier":
		_required(data, "supplier_name", "supplier_group")
		for field in ("supplier_name", "supplier_group", "supplier_type", "mobile_no", "email_id"):
			doc.set(field, data.get(field))
	elif master_type == "master-store":
		_required(data, "warehouse_name", "company", "parent_warehouse")
		for field in ("warehouse_name", "company", "parent_warehouse"):
			doc.set(field, data.get(field))
	else:
		_required(data, "attribute_name", "values")
		doc.attribute_name = data["attribute_name"]
		doc.numeric_values = 0
		doc.set("item_attribute_values", [])
		for value in _attribute_values(data["values"]):
			doc.append("item_attribute_values", {"attribute_value": value, "abbr": value[:10]})
	doc.save()
	return {"name": doc.name, "doctype": doc.doctype, "action": "updated"}


def _list(doctype, fields, filters=None):
	return frappe.get_list(doctype, fields=fields, filters=filters or {}, order_by="modified desc", limit_page_length=1000)


def _raisoni_master_list(doctype, fields):
	if frappe.local.site != MASTER_EDIT_SITE or not frappe.db.exists("DocType", doctype):
		return []
	return _list(doctype, fields, {"enabled": 1})


def _required(data, *fields):
	missing = [field.replace("_", " ").title() for field in fields if not data.get(field)]
	if missing:
		frappe.throw(f"Please fill: {', '.join(missing)}")


def _default_company():
	return frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company") or frappe.db.get_value("Company")


def _project_company(project):
	company = frappe.db.get_value("Project", project, "company")
	if not company:
		frappe.throw("Selected Project has no Company")
	return company


def _project(data):
	if frappe.local.site not in SIMPLE_MASTER_SITES:
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
	if frappe.local.site not in SIMPLE_MASTER_SITES:
		return _site_full(data)
	if frappe.local.site == MASTER_EDIT_SITE:
		_required(data, "site_name", "project")
		doc = frappe.new_doc("CMR Site")
		doc.site_name = data["site_name"]
		doc.project = data["project"]
		doc.company = _project_company(data["project"])
		doc.status = "Active"
		return doc
	_required(data, "site_name")
	doc = frappe.new_doc("CMR Site")
	doc.site_name = data["site_name"]
	doc.company = None
	doc.project = None
	doc.status = "Active"
	doc.flags.ignore_mandatory = True
	return doc


def _zone(data):
	_check_master_edit_site()
	_required(data, "zone_name", "project", "site")
	doc = frappe.new_doc("CMR Zone")
	for field in ("zone_name", "project", "site", "enabled"):
		doc.set(field, data.get(field))
	return doc


def _village(data):
	_check_master_edit_site()
	_required(data, "village_name", "project", "site", "zone")
	doc = frappe.new_doc("CMR Village")
	for field in ("village_name", "project", "site", "zone", "enabled"):
		doc.set(field, data.get(field))
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
	doc.is_stock_item = 1 if data.get("is_stock_item", 1) else 0
	doc.description = data.get("description") or data["item_name"]
	_set_item_classification(doc, data)
	return doc


def _set_item_classification(doc, data):
	for fieldname in ("custom_cmr_material_type", "custom_cmr_moc", "custom_cmr_pressure_rating", "custom_cmr_diameter"):
		if doc.meta.has_field(fieldname):
			doc.set(fieldname, data.get(fieldname))


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


def _attribute_values(values):
	return list(dict.fromkeys(part.strip() for part in (values or "").split(",") if part.strip()))


def _attribute(data):
	_required(data, "attribute_name", "values")
	doc = frappe.new_doc("Item Attribute")
	doc.attribute_name = data["attribute_name"]
	doc.numeric_values = 0
	for value in _attribute_values(data["values"]):
		doc.append("item_attribute_values", {"attribute_value": value, "abbr": value[:10]})
	return doc
