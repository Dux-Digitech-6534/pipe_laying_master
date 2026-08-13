import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt


class CMRPipeLayingMeasurement(Document):
	def validate(self):
		self._calculate_quantities()
		self._validate_segments()

	def before_submit(self):
		self.status = "Approved"

	def on_submit(self):
		from cmr_pipe_laying_master.services.stock import create_execution_consumption

		self.db_set("stock_entry", create_execution_consumption(self))

	def on_cancel(self):
		from cmr_pipe_laying_master.services.stock import cancel_linked_stock_entry

		cancel_linked_stock_entry(self.stock_entry)

	def _calculate_quantities(self):
		self.total_actual_length = sum(flt(row.actual_length) for row in self.segments)
		for row in self.excavation_details:
			row.width = row.width or self.pipe_width
			row.calculated_qty = flt(row.length) * flt(row.width) * flt(row.calculated_depth)
			row.actual_qty = flt(row.length) * flt(row.width) * flt(row.actual_depth)
		for row in self.refill_details:
			row.length = row.length or self.total_actual_length
			row.width = row.width or self.pipe_width
			row.quantity = flt(row.length) * flt(row.width) * flt(row.depth)
		self.total_excavation_qty = sum(flt(row.actual_qty) for row in self.excavation_details)
		self.total_refill_qty = sum(flt(row.quantity) for row in self.refill_details)

	def _validate_segments(self):
		if not self.segments:
			frappe.throw("At least one pipe segment is required")
		for row in self.segments:
			if flt(row.chainage_to) < flt(row.chainage_from):
				frappe.throw(f"Row {row.idx}: Chainage To cannot be less than Chainage From")
			if flt(row.actual_length) <= 0:
				frappe.throw(f"Row {row.idx}: Actual Laid Length must be greater than zero")
			row.restoration_required = cint(self.restoration_required)
			if cint(self.restoration_required) and row.restoration_status != "Completed":
				row.restoration_status = "Pending"
			elif not cint(self.restoration_required):
				row.restoration_status = "Not Required"
