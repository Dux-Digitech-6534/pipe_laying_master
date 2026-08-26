import frappe
from frappe.model.document import Document
from frappe.utils import flt


class CMRValveInstallation(Document):
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
		if flt(self.quantity) <= 0:
			frappe.throw("Valve Quantity must be greater than zero")

		item = frappe.get_cached_doc("Item", self.valve_item)
		if item.disabled or not item.is_stock_item or not item.stock_uom:
			frappe.throw("Select an enabled stock Valve Item with a Stock UOM")
		self.uom = item.stock_uom
		if frappe.local.site == RAISONI_SITE:
			from cmr_pipe_laying_master.services.stock import get_item_operational_details, validate_execution_item_type

			details = get_item_operational_details(self.valve_item, self.contractor_warehouse)
			validate_execution_item_type(self.valve_item, "Valve", details.material_type)
			self.moc = details.moc
			self.pressure_rating = details.pressure_rating
			self.diameter = details.diameter
			self.current_stock = details.current_stock
			self._validate_fittings(get_item_operational_details, validate_execution_item_type)
			self.total_fitting_qty = flt(sum(flt(row.quantity) for row in self.fittings), 3)
			if flt(self.gps_accuracy) < 0:
				frappe.throw("GPS Accuracy cannot be negative")
		if not self._segment_name():
			frappe.throw("Selected Pipe No does not belong to the selected Pipe Laying Measurement")

		if frappe.local.site == RAISONI_SITE and self.docstatus == 1:
			if not self.gps_latitude or not self.gps_longitude:
				frappe.throw("Please capture GPS location before submitting.")
			if not -90 <= flt(self.gps_latitude) <= 90:
				frappe.throw("GPS Latitude must be between -90 and 90")
			if not -180 <= flt(self.gps_longitude) <= 180:
				frappe.throw("GPS Longitude must be between -180 and 180")

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

	def _validate_fittings(self, detail_loader, type_validator):
		for row in self.fittings:
			if not row.item_code:
				frappe.throw(f"Valve Fitting row {row.idx}: Fitting Item is required")
			item = frappe.get_cached_doc("Item", row.item_code)
			if item.disabled or not item.is_stock_item or not item.stock_uom:
				frappe.throw(f"Valve Fitting row {row.idx}: select an enabled stock Item with a Stock UOM")
			if flt(row.quantity) <= 0:
				frappe.throw(f"Valve Fitting row {row.idx}: Quantity must be greater than zero")
			row.quantity = flt(row.quantity, 3)
			details = detail_loader(row.item_code, self.contractor_warehouse)
			type_validator(row.item_code, "Fitting", details.material_type)
			row.uom = details.uom
			row.moc = details.moc
			row.pressure_rating = details.pressure_rating
			row.diameter = details.diameter
			row.current_stock = details.current_stock

	def _segment_name(self):
		return frappe.db.get_value("CMR Pipe Segment", {"parent": self.pipe_measurement, "pipe_no": self.pipe_no}, "name")
