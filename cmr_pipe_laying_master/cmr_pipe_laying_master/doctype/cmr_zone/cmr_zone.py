import frappe
from frappe.model.document import Document


class CMRZone(Document):
	def validate(self):
		site_project = frappe.db.get_value("CMR Site", self.site, "project")
		if site_project != self.project:
			frappe.throw("Selected Site does not belong to the selected Project")

