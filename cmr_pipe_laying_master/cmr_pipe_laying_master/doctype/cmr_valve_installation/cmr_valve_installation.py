import frappe
from frappe.model.document import Document
from frappe.utils import flt


class CMRValveInstallation(Document):
	def validate(self):
		if flt(self.quantity) <= 0:
			frappe.throw("Valve Quantity must be greater than zero")
		if not self._segment_name():
			frappe.throw("Selected Pipe No does not belong to the selected Pipe Laying Measurement")

	def before_submit(self):
		self.status = "Completed"

	def on_submit(self):
		from cmr_pipe_laying_master.services.stock import create_execution_consumption

		self.db_set("stock_entry", create_execution_consumption(self))
		frappe.db.set_value("CMR Pipe Segment", self._segment_name(), "valve_status", "Completed")

	def on_cancel(self):
		from cmr_pipe_laying_master.services.stock import cancel_linked_stock_entry

		cancel_linked_stock_entry(self.stock_entry)
		segment = self._segment_name()
		if segment:
			frappe.db.set_value("CMR Pipe Segment", segment, "valve_status", "Pending")

	def _segment_name(self):
		return frappe.db.get_value("CMR Pipe Segment", {"parent": self.pipe_measurement, "pipe_no": self.pipe_no}, "name")
