import frappe
from frappe.model.document import Document
from frappe.utils import flt


class CMRRoadRestoration(Document):
	def validate(self):
		self.m15_quantity = flt(self.m15_length) * flt(self.pipe_width) * flt(self.m15_depth)
		self.m20_quantity = flt(self.m20_length) * flt(self.pipe_width) * flt(self.m20_depth)
		self.m30_quantity = flt(self.m30_length) * flt(self.pipe_width) * flt(self.m30_depth)
		if not self._segment_name():
			frappe.throw("Selected Pipe No does not belong to the selected Pipe Laying Measurement")

	def before_submit(self):
		self.status = "Completed"

	def on_submit(self):
		frappe.db.set_value("CMR Pipe Segment", self._segment_name(), "restoration_status", "Completed")

	def on_cancel(self):
		segment = self._segment_name()
		if segment:
			frappe.db.set_value("CMR Pipe Segment", segment, "restoration_status", "Pending")

	def _segment_name(self):
		return frappe.db.get_value("CMR Pipe Segment", {"parent": self.pipe_measurement, "pipe_no": self.pipe_no}, "name")
