import frappe
from frappe.model.document import Document


class CMRVillage(Document):
	def validate(self):
		site_project = frappe.db.get_value("CMR Site", self.site, "project")
		if site_project != self.project:
			frappe.throw("Selected Site does not belong to the selected Project")

		zone = frappe.db.get_value("CMR Zone", self.zone, ["project", "site"], as_dict=True)
		if not zone or zone.project != self.project or zone.site != self.site:
			frappe.throw("Selected Zone does not belong to the selected Project and Site")

