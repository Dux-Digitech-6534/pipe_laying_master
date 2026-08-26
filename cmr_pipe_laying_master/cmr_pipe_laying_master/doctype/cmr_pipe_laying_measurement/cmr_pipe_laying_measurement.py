from math import isfinite

import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt


MEASUREMENT_PRECISION = 3


class CMRPipeLayingMeasurement(Document):
	def validate(self):
		from cmr_pipe_laying_master.services.hierarchy import RAISONI_SITE, validate_location_hierarchy

		validate_location_hierarchy(self.project, self.site, self.zone, self.village)
		strict_calculations = frappe.local.site == RAISONI_SITE
		self._validate_segments(strict_calculations)
		if strict_calculations:
			self._validate_fittings()
		self._calculate_quantities(strict_calculations)

	def before_submit(self):
		self.status = "Approved"

	def on_submit(self):
		from cmr_pipe_laying_master.services.stock import create_execution_consumption

		self.db_set("stock_entry", create_execution_consumption(self))

	def on_cancel(self):
		from cmr_pipe_laying_master.services.stock import cancel_linked_stock_entry

		cancel_linked_stock_entry(self.stock_entry)

	def _calculate_quantities(self, strict=False):
		if strict and flt(self.pipe_width) <= 0:
			frappe.throw("Trench / Pipe Width must be greater than zero")
		self.total_actual_length = _rounded(sum(flt(row.actual_length) for row in self.segments))
		for row in self.excavation_details:
			if strict:
				length = _non_negative(row.length, "Length", row.idx, "Excavation")
				width = _non_negative(row.width, "Width", row.idx, "Excavation")
				calculated_depth = _non_negative(row.calculated_depth, "Calculated Depth", row.idx, "Excavation")
				actual_depth = _non_negative(row.actual_depth, "Actual Depth", row.idx, "Excavation")
			else:
				row.width = row.width or self.pipe_width
				length = flt(row.length)
				width = flt(row.width)
				calculated_depth = flt(row.calculated_depth)
				actual_depth = flt(row.actual_depth)
			row.calculated_qty = _rounded(length * width * calculated_depth)
			row.actual_qty = _rounded(length * width * actual_depth)
		for row in self.refill_details:
			if strict:
				length = _non_negative(row.length, "Length", row.idx, "Refill")
				width = _non_negative(row.width, "Width", row.idx, "Refill")
				depth = _non_negative(row.depth, "Depth", row.idx, "Refill")
			else:
				row.length = row.length or self.total_actual_length
				row.width = row.width or self.pipe_width
				length = flt(row.length)
				width = flt(row.width)
				depth = flt(row.depth)
			row.quantity = _rounded(length * width * depth)
		self.total_excavation_qty = _rounded(sum(flt(row.actual_qty) for row in self.excavation_details))
		self.total_refill_qty = _rounded(sum(flt(row.quantity) for row in self.refill_details))
		if strict and self.meta.has_field("total_fitting_qty"):
			self.total_fitting_qty = _rounded(sum(flt(row.quantity) for row in self.fittings))

	def _validate_segments(self, strict=False):
		if not self.segments:
			frappe.throw("At least one pipe segment is required")
		for row in self.segments:
			if strict:
				chainage_from = _non_negative(row.chainage_from, "Chainage From", row.idx, "Pipe Segment")
				chainage_to = _non_negative(row.chainage_to, "Chainage To", row.idx, "Pipe Segment")
				if chainage_from == chainage_to:
					frappe.throw(f"Pipe Segment row {row.idx}: Chainage From and Chainage To cannot be equal")
				row.chainage_length = _rounded(abs(chainage_to - chainage_from))
				self._validate_stock_item(row.pipe_item, "Pipe Item", row.idx, "Pipe Segment", expected_type="Pipe")
				self._populate_item_details(row, row.pipe_item)
			elif flt(row.chainage_to) < flt(row.chainage_from):
				frappe.throw(f"Row {row.idx}: Chainage To cannot be less than Chainage From")
			if strict:
				actual_length = _number(row.actual_length, "Actual Laid Length", row.idx, "Pipe Segment")
				if actual_length <= 0:
					frappe.throw(f"Row {row.idx}: Actual Laid Length must be greater than zero")
				row.actual_length = _rounded(actual_length)
			elif flt(row.actual_length) <= 0:
				frappe.throw(f"Row {row.idx}: Actual Laid Length must be greater than zero")
			row.restoration_required = cint(self.restoration_required)
			if cint(self.restoration_required) and row.restoration_status != "Completed":
				row.restoration_status = "Pending"
			elif not cint(self.restoration_required):
				row.restoration_status = "Not Required"

	def _validate_fittings(self):
		for row in self.fittings:
			item = self._validate_stock_item(row.item_code, "Fitting Item", row.idx, "Fitting", expected_type="Fitting")
			quantity = _number(row.quantity, "Quantity", row.idx, "Fitting")
			if quantity <= 0:
				frappe.throw(f"Fitting row {row.idx}: Quantity must be greater than zero")
			row.quantity = _rounded(quantity)
			row.uom = item.stock_uom
			self._populate_item_details(row, row.item_code)
			latitude = _number(row.gps_latitude, "GPS Latitude", row.idx, "Fitting")
			longitude = _number(row.gps_longitude, "GPS Longitude", row.idx, "Fitting")
			if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
				frappe.throw(f"Fitting row {row.idx}: GPS coordinates are outside the valid range")

	def _populate_item_details(self, row, item_code):
		from cmr_pipe_laying_master.services.stock import get_item_operational_details

		details = get_item_operational_details(item_code, self.contractor_warehouse)
		row.moc = details.moc
		row.pressure_rating = details.pressure_rating
		row.diameter = details.diameter
		row.current_stock = details.current_stock

	@staticmethod
	def _validate_stock_item(item_code, label, row_index, table_label, expected_type=None):
		if not item_code:
			frappe.throw(f"{table_label} row {row_index}: {label} is required")
		item = frappe.get_cached_doc("Item", item_code)
		if item.disabled:
			frappe.throw(f"{table_label} row {row_index}: {label} {item_code} is disabled")
		if not item.is_stock_item or not item.stock_uom:
			frappe.throw(f"{table_label} row {row_index}: {label} {item_code} must be an enabled stock item with a Stock UOM")
		if expected_type:
			from cmr_pipe_laying_master.services.stock import validate_execution_item_type

			validate_execution_item_type(item_code, expected_type)
		return item


def _number(value, label, row_index, table_label):
	try:
		number = float(value or 0)
	except (TypeError, ValueError):
		frappe.throw(f"{table_label} row {row_index}: {label} must be numeric")
	if not isfinite(number):
		frappe.throw(f"{table_label} row {row_index}: {label} must be a finite number")
	return number


def _non_negative(value, label, row_index, table_label):
	number = _number(value, label, row_index, table_label)
	if number < 0:
		frappe.throw(f"{table_label} row {row_index}: {label} cannot be negative")
	return number


def _rounded(value):
	return flt(value, MEASUREMENT_PRECISION)
