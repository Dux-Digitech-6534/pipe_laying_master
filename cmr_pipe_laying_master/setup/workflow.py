import frappe


WORKFLOW_NAME = "CMR Pipe Laying Approval"


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
	for state, doc_status, role in (
		("Draft", "0", "CMR Site Engineer"),
		("Pending Approval", "0", "CMR Project Manager"),
		("Rejected", "0", "CMR Site Engineer"),
		("Approved", "1", "CMR Project Manager"),
	):
		workflow.append("states", {"state": state, "doc_status": doc_status, "allow_edit": role})
	for state, action, next_state, role in (
		("Draft", "Send for Approval", "Pending Approval", "CMR Site Engineer"),
		("Rejected", "Send for Approval", "Pending Approval", "CMR Site Engineer"),
		("Pending Approval", "Approve", "Approved", "CMR Project Manager"),
		("Pending Approval", "Reject", "Rejected", "CMR Project Manager"),
		("Rejected", "Revise", "Draft", "CMR Site Engineer"),
		("Draft", "Send for Approval", "Pending Approval", "CMR Pipe Admin"),
		("Rejected", "Send for Approval", "Pending Approval", "CMR Pipe Admin"),
		("Pending Approval", "Approve", "Approved", "CMR Pipe Admin"),
		("Pending Approval", "Reject", "Rejected", "CMR Pipe Admin"),
		("Pending Approval", "Approve", "Approved", "System Manager"),
		("Pending Approval", "Reject", "Rejected", "System Manager"),
	):
		workflow.append("transitions", {
			"state": state, "action": action, "next_state": next_state,
			"allowed": role, "allow_self_approval": 0,
		})
	workflow.save(ignore_permissions=True)
	frappe.clear_cache(doctype="CMR Pipe Laying Measurement")
	return workflow.name
