import frappe


CMR_ROLES = (
	"CMR Pipe Admin",
	"CMR Master Manager",
	"CMR Store User",
	"CMR Site Engineer",
	"CMR Project Manager",
	"CMR Pipe Viewer",
)

MASTER_DOCTYPES = ("CMR Site", "CMR Contractor Assignment")
TRANSACTION_DOCTYPES = (
	"CMR Pipe Laying Measurement",
	"CMR Valve Installation",
	"CMR Road Restoration",
)


def sync_permissions():
	for doctype in MASTER_DOCTYPES:
		_sync_doctype_permissions(doctype, _master_permissions())
	for doctype in TRANSACTION_DOCTYPES:
		_sync_doctype_permissions(doctype, _transaction_permissions())
	frappe.clear_cache()
	return sum(len(_master_permissions()) for _ in MASTER_DOCTYPES) + sum(
		len(_transaction_permissions()) for _ in TRANSACTION_DOCTYPES
	)


def _sync_doctype_permissions(doctype, permissions):
	for role in CMR_ROLES:
		for name in frappe.get_all(
			"Custom DocPerm",
			filters={"parent": doctype, "role": role, "permlevel": 0},
			pluck="name",
		):
			frappe.delete_doc("Custom DocPerm", name, force=True, ignore_permissions=True)
	for permission in permissions:
		frappe.get_doc({
			"doctype": "Custom DocPerm", "parent": doctype,
			"parenttype": "DocType", "parentfield": "permissions", "permlevel": 0,
			**permission,
		}).insert(ignore_permissions=True)


def _base(role, **rights):
	permission = {
		"role": role, "read": 1, "report": 1, "print": 1,
		"email": 1, "share": 0, "export": 0,
	}
	permission.update(rights)
	return permission


def _master_permissions():
	return (
		_base("CMR Pipe Admin", write=1, create=1, delete=1, export=1, share=1),
		_base("CMR Master Manager", write=1, create=1, delete=1, export=1),
		_base("CMR Store User"), _base("CMR Site Engineer"),
		_base("CMR Project Manager", export=1), _base("CMR Pipe Viewer"),
	)


def _transaction_permissions():
	return (
		_base("CMR Pipe Admin", write=1, create=1, delete=1, submit=1, cancel=1, amend=1, export=1, share=1),
		_base("CMR Site Engineer", write=1, create=1, delete=1),
		_base("CMR Project Manager", write=1, submit=1, cancel=1, amend=1, export=1),
		_base("CMR Master Manager"), _base("CMR Store User"), _base("CMR Pipe Viewer"),
	)
