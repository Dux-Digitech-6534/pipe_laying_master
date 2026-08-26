from math import isfinite

import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt


RESTORATION_PRECISION = 3


class CMRRoadRestoration(Document):
	def validate(self):
		from cmr_pipe_laying_master.services.hierarchy import RAISONI_SITE, validate_location_hierarchy, validate_measurement_location

		validate_location_hierarchy(self.project, self.site, self.zone, self.village)
		validate_measurement_location(
			self.pipe_measurement,
			self.project,
			self.site,
			self.zone,
			self.village,
			company=self.company,
			contractor_assignment=self.contractor_assignment,
		)
		strict = frappe.local.site == RAISONI_SITE
		if strict:
			self._validate_dimensions()
			self._validate_optional_gps()
		self._calculate_quantities()
		self._validate_segment(strict)

	def before_submit(self):
		self.status = "Completed"

	def on_submit(self):
		frappe.db.set_value("CMR Pipe Segment", self._segment_name(), "restoration_status", "Completed")

	def on_cancel(self):
		segment = self._segment_name()
		if segment:
			frappe.db.set_value("CMR Pipe Segment", segment, "restoration_status", "Pending")

	def _validate_dimensions(self):
		restoration_length = _non_negative(self.pipe_length, "Restoration Length")
		restoration_width = _non_negative(self.pipe_width, "Restoration Width")
		if restoration_length <= 0:
			frappe.throw("Restoration Length must be greater than zero")
		if restoration_width <= 0:
			frappe.throw("Restoration Width must be greater than zero")

		dismantling_length = _non_negative(self.dismantling_length, "Dismantling Length")
		_non_negative(self.dismantling_depth, "Dismantling Depth")
		if dismantling_length > restoration_length:
			frappe.throw("Dismantling Length cannot exceed Restoration Length")

		for grade in ("M15", "M20", "M30"):
			length = _non_negative(self.get(f"{grade.lower()}_length"), f"{grade} Length")
			_non_negative(self.get(f"{grade.lower()}_depth"), f"{grade} Depth")
			if length > restoration_length:
				frappe.throw(f"{grade} Length cannot exceed Restoration Length")

	def _calculate_quantities(self):
		width = flt(self.pipe_width)
		self.dismantling_quantity = _rounded(flt(self.dismantling_length) * width * flt(self.dismantling_depth))
		total_concrete = 0
		for grade in ("m15", "m20", "m30"):
			quantity = _rounded(flt(self.get(f"{grade}_length")) * width * flt(self.get(f"{grade}_depth")))
			self.set(f"{grade}_quantity", quantity)
			total_concrete += quantity
		self.total_concrete_quantity = _rounded(total_concrete)

	def _validate_optional_gps(self):
		_validate_gps_pair(self.gps_latitude_from, self.gps_longitude_from, "From")
		_validate_gps_pair(self.gps_latitude_to, self.gps_longitude_to, "To")

	def _validate_segment(self, strict=False):
		segment = frappe.db.get_value(
			"CMR Pipe Segment",
			{"parent": self.pipe_measurement, "pipe_no": self.pipe_no},
			["name", "restoration_required", "restoration_status"],
			as_dict=True,
		)
		if not segment:
			frappe.throw("Selected Pipe No does not belong to the selected Pipe Laying Measurement")
		if strict and (not cint(segment.restoration_required) or segment.restoration_status == "Not Required"):
			frappe.throw("Road Restoration is not required for the selected Pipe No")
		if strict and segment.restoration_status == "Completed":
			frappe.throw("Road Restoration is already completed for the selected Pipe No")

	def _segment_name(self):
		return frappe.db.get_value("CMR Pipe Segment", {"parent": self.pipe_measurement, "pipe_no": self.pipe_no}, "name")


def _number(value, label):
	try:
		number = float(value or 0)
	except (TypeError, ValueError):
		frappe.throw(f"{label} must be numeric")
	if not isfinite(number):
		frappe.throw(f"{label} must be a finite number")
	return number


def _non_negative(value, label):
	number = _number(value, label)
	if number < 0:
		frappe.throw(f"{label} cannot be negative")
	return number


def _validate_gps_pair(latitude, longitude, label):
	if latitude in (None, "") and longitude in (None, ""):
		return
	if latitude in (None, "") or longitude in (None, ""):
		frappe.throw(f"{label} GPS Latitude and Longitude must be captured together")
	latitude = _number(latitude, f"{label} GPS Latitude")
	longitude = _number(longitude, f"{label} GPS Longitude")
	if not -90 <= latitude <= 90:
		frappe.throw(f"{label} GPS Latitude must be between -90 and 90")
	if not -180 <= longitude <= 180:
		frappe.throw(f"{label} GPS Longitude must be between -180 and 180")


def _rounded(value):
	return flt(value, RESTORATION_PRECISION)
