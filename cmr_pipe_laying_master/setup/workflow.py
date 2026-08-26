import frappe


WORKFLOW_NAME = "CMR Pipe Laying Approval"


def disable_workflow():
	"""Keep Raisoni on the normal ERPNext Draft -> Submitted lifecycle."""
	if frappe.db.exists("Workflow", WORKFLOW_NAME):
		frappe.db.set_value("Workflow", WORKFLOW_NAME, "is_active", 0)
	frappe.clear_cache(doctype="CMR Pipe Laying Measurement")
	return None


def sync_workflow():
	for state in ("Draft", "Pending Approval", "Approved", "Rejected"):
		if not frappe.db.exists("Workflow State", state):
			frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": state}).insert(ignore_permissions=True)
	for action in ("Send for Approval", "Approve", "Reject", "Revise"):
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": action}).insert(ignore_permissions=True)
	if frappe.db.exists("Workflow", WORKFLOW_NAME):
		workflow = frappe.get_doc("Workflow", WORKFLOW_NAME)
		workflow.states = []
		workflow.transitions = []
	else:
		workflow = frappe.new_doc("Workflow")
		workflow.workflow_name = WORKFLOW_NAME
	workflow.document_type = "CMR Pipe Laying Measurement"
	workflow.is_active = 1
	workflow.workflow_state_field = "status"
	workflow.send_email_alert = 0
	for state, doc_status in (
		("Draft", "0"),
		("Pending Approval", "0"),
		("Rejected", "0"),
		("Approved", "1"),
	):
		workflow.append("states", {"state": state, "doc_status": doc_status, "allow_edit": "System Manager"})
	for state, action, next_state in (
		("Draft", "Send for Approval", "Pending Approval"),
		("Rejected", "Send for Approval", "Pending Approval"),
		("Pending Approval", "Approve", "Approved"),
		("Pending Approval", "Reject", "Rejected"),
		("Rejected", "Revise", "Draft"),
	):
		workflow.append("transitions", {
			"state": state, "action": action, "next_state": next_state,
			"allowed": "System Manager", "allow_self_approval": 0,
		})
	workflow.save(ignore_permissions=True)
	frappe.clear_cache(doctype="CMR Pipe Laying Measurement")
	return workflow.name
