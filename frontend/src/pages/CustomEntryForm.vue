<script setup>
import { computed, onMounted, ref, watch } from "vue";
import "../modern-form.css";
import SearchSelect from "../components/forms/SearchSelect.vue";

const props = defineProps({ pageKey: { type: String, required: true }, title: String, recordName: { type: String, default: "" }, hierarchyEnabled: { type: Boolean, default: false } });
const emit = defineEmits(["close", "saved", "create-master", "return-material", "edit-return"]);
const today = new Date().toISOString().slice(0, 10);
const loading = ref(true);
const saving = ref(false);
const error = ref("");
const success = ref(null);
const options = ref({ companies: [], projects: [], sites: [], zones: [], villages: [], suppliers: [], warehouses: [], items: [], item_attributes: {}, select_options: {}, contractors: [], measurements: [], users: [], purchase_orders: [], purchase_receipts: [], purchase_tax_templates: [] });
const form = ref({});
const activeRecordName = ref(props.recordName || "");
const documentInfo = ref(null);
const purchaseReturns = ref(null);
const measurementSegments = ref([]);
const loadingSegments = ref(false);
const gpsAccuracy = ref(null);
const gpsMessage = ref("");
const gpsMessageType = ref("");
const gpsCapturing = ref(false);
const restorationGpsTarget = ref("");
const attachmentFields = [
  { field: "invoice_attachment", label: "Invoice" },
  { field: "test_report_attachment", label: "Test Report" },
  { field: "bilty_attachment", label: "Bilty" },
];

const isMaterial = computed(() => ["material-inward", "material-issue"].includes(props.pageKey) || (!props.hierarchyEnabled && props.pageKey === "material-return"));
const isTransfer = computed(() => props.pageKey === "material-issue" || (!props.hierarchyEnabled && props.pageKey === "material-return"));
const hasLocationHierarchy = computed(() => props.hierarchyEnabled && ["pipe-laying", "valves", "restoration"].includes(props.pageKey));
const isRaisoniReferenceEntry = computed(() => props.hierarchyEnabled && ["valves", "restoration"].includes(props.pageKey));
const isRaisoniValve = computed(() => props.hierarchyEnabled && props.pageKey === "valves");
const isRaisoniRestoration = computed(() => props.hierarchyEnabled && props.pageKey === "restoration");
const filteredWarehouses = computed(() => options.value.warehouses.filter(row => !form.value.company || row.company === form.value.company));
const filteredTargetWarehouses = computed(() => filteredWarehouses.value.filter(row => row.name !== form.value.source_warehouse));
const filteredSites = computed(() => options.value.sites.filter(row => form.value.project && row.project === form.value.project));
const filteredContractors = computed(() => (options.value.contractors || []).filter(row => form.value.project && form.value.site && row.project === form.value.project && row.site === form.value.site));
const filteredZones = computed(() => (options.value.zones || []).filter(row => form.value.project && form.value.site && row.project === form.value.project && row.site === form.value.site));
const filteredVillages = computed(() => (options.value.villages || []).filter(row => form.value.project && form.value.site && form.value.zone && row.project === form.value.project && row.site === form.value.site && row.zone === form.value.zone));
const filteredMeasurements = computed(() => {
  if (isRaisoniReferenceEntry.value || !hasLocationHierarchy.value) return options.value.measurements;
  if (!form.value.project || !form.value.site || !form.value.zone || !form.value.village) return [];
  return options.value.measurements.filter(row => row.project === form.value.project && row.site === form.value.site && row.zone === form.value.zone && row.village === form.value.village);
});
const hasGpsLocation = computed(() =>
  form.value.gps_latitude !== null && form.value.gps_latitude !== "" && form.value.gps_latitude !== undefined &&
  form.value.gps_longitude !== null && form.value.gps_longitude !== "" && form.value.gps_longitude !== undefined
);
const gpsButtonLabel = computed(() => hasGpsLocation.value ? "Refresh Location" : "Capture GPS Location");
const submitLabel = computed(() => props.pageKey === "pipe-laying" && !props.hierarchyEnabled ? "Send for Approval" : "Save & Submit");
const isEditing = computed(() => Boolean(activeRecordName.value));
const isReadOnly = computed(() => Boolean(documentInfo.value && documentInfo.value.docstatus !== 0));
const statusLabel = computed(() => documentInfo.value?.docstatus === 0 ? "Draft" : documentInfo.value?.docstatus === 1 ? (documentInfo.value.status || "Submitted") : "Cancelled");
const formHeading = computed(() => !isEditing.value ? `New ${props.title}` : isReadOnly.value ? `View ${props.title}` : `Edit ${props.title}`);
const totalPipeLaidLength = computed(() => measurementTotal(form.value.segments, "actual_length"));
const totalExcavationQty = computed(() => measurementTotal(form.value.excavation_details, "actual_qty"));
const totalRefillQty = computed(() => measurementTotal(form.value.refill_details, "quantity"));
const totalFittingQty = computed(() => measurementTotal(form.value.fittings, "quantity"));
const totalConcreteQuantity = computed(() => roundedMeasurement(["m15", "m20", "m30"].reduce((total, grade) => total + concreteQtyNumber(grade), 0)));
const totalMaterialQuantity = computed(() => roundedMeasurement((form.value.items || []).reduce((total, row) => total + measurementNumber(row.qty), 0)));
const totalSupplyCost = computed(() => roundedMeasurement((form.value.items || []).reduce((total, row) => total + amount(row), 0)));
const finalMaterialTotal = computed(() => roundedMeasurement(totalSupplyCost.value + measurementNumber(form.value.transport_cost)));
const breakupItems = computed(() => {
  const catalog = new Map((options.value.items || []).map(item => [item.item_code || item.name, item]));
  return (form.value.items || [])
    .filter(row => row.item_code)
    .map(row => {
      const item = catalog.get(row.item_code) || {};
      return { ...item, ...row, item_code: row.item_code, item_name: item.item_name || row.item_code, material_type: row.material_type || item.material_type || "" };
    })
    .filter(row => row.material_type === "Pipe");
});
const dismantlingQuantity = computed(() => roundedMeasurement(measurementNumber(form.value.dismantling_length) * measurementNumber(form.value.pipe_width) * measurementNumber(form.value.dismantling_depth)));

function blankItem() { return { item_code: "", qty: 1, rate: 0, uom: "", material_type: "", moc: "", pressure_rating: "", diameter: "", consumable_type: "Consumable", purchase_order: "", purchase_order_item: "", source_stock: 0, target_stock: 0 }; }
function blankSegment() { return { pipe_no: "", pipe_item: "", start_node: "", end_node: "", chainage_from: 0, chainage_to: 0, chainage_length: 0, actual_length: 0, diameter: 0, moc: "", pressure_rating: "", current_stock: 0 }; }
function blankExcavation() { return { excavation_type: "Excavation Ordinary Soil", length: 0, width: 0, calculated_depth: 0, actual_depth: 0, calculated_qty: 0, actual_qty: 0 }; }
function blankRefill() { return { material_type: "Sand", length: 0, width: 0, depth: 0, quantity: 0 }; }
function blankFitting() { return { item_code: "", quantity: 1, uom: "", junction_no: "", gps_latitude: null, gps_longitude: null, current_stock: 0, moc: "", pressure_rating: "", diameter: 0 }; }
function blankBreakup() { return { item_code: "", pipe_or_roll: "Pipe", nos: 1, length: 0, total_length: 0 }; }

function resetForm() {
  success.value = null; error.value = ""; documentInfo.value = null; purchaseReturns.value = null; activeRecordName.value = "";
  measurementSegments.value = [];
  gpsAccuracy.value = null;
  gpsMessage.value = "";
  gpsMessageType.value = "";
  restorationGpsTarget.value = "";
  if (props.pageKey === "material-inward") form.value = { posting_date: today, company: "", project: "", supplier: "", site: "", warehouse: "", po_number: "", supplier_delivery_note: "", mrn_no: "", vehicle_type: "Truck", vehicle_no: "", transporter_name: "", transport_cost: 0, driver_name: "", driver_mobile: "", lr_no: "", invoice_no: "", invoice_date: "", invoice_status: "Pending", invoice_attachment: "", test_report_attachment: "", bilty_attachment: "", remarks: "", items: [blankItem()], quantity_breakup: [] };
  else if (isTransfer.value) form.value = { posting_date: today, company: "", project: "", site: "", contractor_assignment: "", source_warehouse: "", target_warehouse: "", receiver: "", remarks: "", items: [blankItem()] };
  else if (props.pageKey === "pipe-laying") form.value = { laying_date: today, company: "", project: "", site: "", zone: "", village: "", type_of_work: "Distribution Pipe Laying", laying_mode: "Single", trench_method: "Open Trench", section_incharge: "", contractor_assignment: "", pipe_width: 0, restoration_required: 1, end_cap: "N/A", remarks: "", segments: [blankSegment()], excavation_details: [blankExcavation()], refill_details: [blankRefill()], fittings: [] };
  else if (props.pageKey === "valves") form.value = { installation_date: today, company: "", project: "", site: "", zone: "", village: "", pipe_measurement: "", pipe_no: "", contractor_assignment: "", valve_item: "", quantity: 1, uom: "", moc: "", pressure_rating: "", diameter: 0, current_stock: 0, chamber_size: "", specific_location: "", gps_latitude: null, gps_longitude: null, gps_accuracy: null, total_fitting_qty: 0, remarks: "", fittings: [] };
  else form.value = { restoration_date: today, company: "", project: "", site: "", zone: "", village: "", pipe_measurement: "", pipe_no: "", contractor_assignment: "", pipe_length: 0, pipe_width: 0, restoration_type: "CC Road", dismantling_length: 0, dismantling_depth: 0, dismantling_quantity: 0, m15_length: 0, m15_depth: 0, m20_length: 0, m20_depth: 0, m30_length: 0, m30_depth: 0, total_concrete_quantity: 0, gps_latitude_from: null, gps_longitude_from: null, gps_latitude_to: null, gps_longitude_to: null, remarks: "" };
}

function call(method, args = {}) {
  return new Promise((resolve, reject) => window.frappe.call({ method, args, callback: r => resolve(r.message), error: reject }));
}
async function loadDocument() {
  const result = await call("cmr_pipe_laying_master.api.entries.get_entry_document", { entry_type: props.pageKey, record_name: activeRecordName.value });
  documentInfo.value = result._document || null;
  purchaseReturns.value = result._purchase_returns || null;
  delete result._document;
  delete result._purchase_returns;
  form.value = result;
  gpsAccuracy.value = form.value.gps_accuracy ?? null;
  if (isRaisoniValve.value && documentInfo.value?.docstatus === 0 && Number(form.value.gps_latitude) === 0 && Number(form.value.gps_longitude) === 0) {
    form.value.gps_latitude = null;
    form.value.gps_longitude = null;
  }
  if (isRaisoniRestoration.value && documentInfo.value?.docstatus === 0) {
    for (const target of ["from", "to"]) {
      if (Number(form.value[`gps_latitude_${target}`]) === 0 && Number(form.value[`gps_longitude_${target}`]) === 0) {
        form.value[`gps_latitude_${target}`] = null;
        form.value[`gps_longitude_${target}`] = null;
      }
    }
  }
  recalculatePipeForm();
}
async function loadOptions() {
  loading.value = true; error.value = "";
  try {
    options.value = await call("cmr_pipe_laying_master.api.entries.get_entry_options");
    if (isEditing.value) {
      await loadDocument();
      if (isRaisoniReferenceEntry.value && form.value.pipe_measurement) await loadMeasurementSegments(true);
    } else if (!isRaisoniReferenceEntry.value) {
      const company = options.value.companies?.[0]?.name || "";
      if (!form.value.company) form.value.company = company;
    }
  } catch (e) { error.value = "Form data could not be loaded. Please check document and role permissions."; }
  finally { loading.value = false; }
}
watch(() => [form.value.source_warehouse, form.value.target_warehouse], refreshAllStocks);
watch(() => form.value.company, company => {
  if (isReadOnly.value) return;
  for (const field of ["warehouse", "source_warehouse", "target_warehouse"]) {
    const selected = options.value.warehouses.find(row => row.name === form.value[field]);
    if (selected && company && selected.company !== company) form.value[field] = "";
  }
});
function clearMeasurementReference() {
  if (!["valves", "restoration"].includes(props.pageKey)) return;
  form.value.pipe_measurement = "";
  form.value.pipe_no = "";
  measurementSegments.value = [];
}
function projectChanged() {
  form.value.site = "";
  form.value.contractor_assignment = "";
  if (hasLocationHierarchy.value) {
    form.value.zone = "";
    form.value.village = "";
    clearMeasurementReference();
  }
}
function selectSite(clearContractor = true) {
  const site = options.value.sites.find(x => x.name === form.value.site);
  if (!site) return;
  form.value.company = site.company || form.value.company;
  if (clearContractor) form.value.contractor_assignment = "";
  if (hasLocationHierarchy.value) {
    form.value.zone = "";
    form.value.village = "";
    clearMeasurementReference();
  } else {
    form.value.project = site.project || form.value.project;
    form.value.zone = site.zone || form.value.zone;
    form.value.village = site.village || form.value.village;
  }
  if (props.pageKey === "material-inward" && site.default_warehouse) form.value.warehouse = site.default_warehouse;
  if (props.pageKey === "material-issue" && site.default_warehouse) form.value.source_warehouse = site.default_warehouse;
  if (!props.hierarchyEnabled && props.pageKey === "material-return" && site.default_warehouse) form.value.target_warehouse = site.default_warehouse;

}
function zoneChanged() {
  if (!hasLocationHierarchy.value) return;
  form.value.village = "";
  clearMeasurementReference();
}
function villageChanged() {
  if (hasLocationHierarchy.value) clearMeasurementReference();
}
function applyIssueTargetWarehouse(assignment) {
  const targetWarehouse = assignment?.contractor_warehouse || "";
  if (targetWarehouse && targetWarehouse === form.value.source_warehouse) {
    form.value.target_warehouse = "";
    window.frappe.show_alert({ message: "Contractor Store is the same as Receiving Store. Select a different To Store or update Contractor master.", indicator: "orange" }, 8);
    return;
  }
  form.value.target_warehouse = targetWarehouse;
}
function selectContractor() {
  const assignment = options.value.contractors.find(x => x.name === form.value.contractor_assignment);
  if (!assignment) return;
  const locationChanged = hasLocationHierarchy.value && (
    (assignment.project && assignment.project !== form.value.project) ||
    (assignment.site && assignment.site !== form.value.site)
  );
  form.value.company = assignment.company || form.value.company;
  form.value.project = assignment.project || form.value.project;
  form.value.site = assignment.site || form.value.site;
  if (locationChanged) {
    form.value.zone = "";
    form.value.village = "";
    clearMeasurementReference();
  }
  if (props.pageKey === "material-issue") applyIssueTargetWarehouse(assignment);
  if (!props.hierarchyEnabled && props.pageKey === "material-return") form.value.source_warehouse = assignment.contractor_warehouse || "";

  if (!hasLocationHierarchy.value) selectSite(false);
  refreshAllStocks();
}
async function loadMeasurementSegments(preservePipeNo = false) {
  measurementSegments.value = [];
  if (!form.value.pipe_measurement) {
    form.value.pipe_no = "";
    return;
  }

  loadingSegments.value = true;
  try {
    const rows = await call("cmr_pipe_laying_master.api.entries.get_measurement_segments", {
      pipe_measurement: form.value.pipe_measurement,
      purpose: props.pageKey === "restoration" ? "restoration" : "valve",
    });
    measurementSegments.value = rows || [];
    const currentExists = measurementSegments.value.some(row => row.pipe_no === form.value.pipe_no);
    if (!preservePipeNo) {
      form.value.pipe_no = measurementSegments.value.length === 1 ? measurementSegments.value[0].pipe_no : "";
    } else if (!currentExists && !isReadOnly.value) {
      form.value.pipe_no = "";
    }
  } catch (e) {
    form.value.pipe_no = "";
    error.value = "Pipe segments could not be loaded for the selected measurement.";
  } finally {
    loadingSegments.value = false;
  }
}

async function selectMeasurement() {
  const measurement = options.value.measurements.find(x => x.name === form.value.pipe_measurement);
  if (!measurement) {
    for (const field of ["company", "project", "site", "zone", "village", "contractor_assignment", "pipe_no"]) form.value[field] = "";
    measurementSegments.value = [];
    return;
  }
  for (const field of ["company", "project", "site", "zone", "village", "contractor_assignment"]) {
    form.value[field] = measurement[field] || "";
  }
  if (isRaisoniReferenceEntry.value) await loadMeasurementSegments(false);
}
function itemChanged(row, field = "item_code") {
  const item = options.value.items.find(x => (x.item_code || x.name) === row[field]);
  if (!item) return;
  row.uom = item.stock_uom || row.uom;
  row.material_type = item.material_type || row.material_type;
  row.moc = item.moc || "";
  row.pressure_rating = item.pressure_rating || "";
  row.diameter = item.diameter || 0;
  refreshRowStock(row, field);
}
function selectOptions(key, fallback = []) {
  const configured = options.value.select_options?.[key] || [];
  return configured.length ? configured : fallback;
}
function attributeValues(field, row, priorFields = []) {
  const configured = [...(options.value.item_attributes?.[field] || []), ...(field === "material_type" ? selectOptions("material_type") : [])];
  const itemValues = (options.value.items || [])
    .filter(item => priorFields.every(key => !row[key] || String(item[key] || "") === String(row[key])))
    .map(item => item[field])
    .filter(value => value !== null && value !== undefined && value !== "");
  return [...new Set([...configured, ...itemValues].map(String))].sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
}
function filteredItems(row) {
  return (options.value.items || []).filter(item => ["material_type", "moc", "pressure_rating", "diameter"].every(key => !row[key] || String(item[key] || "") === String(row[key])));
}
function resetItemAfterAttribute(row) { row.item_code = ""; row.uom = ""; row.source_stock = 0; row.target_stock = 0; }
function executionItemsOfType(expectedType) {
  const normalized = String(expectedType || "").trim().toLowerCase();
  return (options.value.items || []).filter(item => String(item.material_type || "").trim().toLowerCase() === normalized);
}
function executionAttributeValues(expectedType, field, row, priorFields = []) {
  const values = executionItemsOfType(expectedType)
    .filter(item => priorFields.every(key => !row[key] || String(item[key] || "") === String(row[key])))
    .map(item => item[field])
    .filter(value => value !== null && value !== undefined && value !== "")
    .map(String);
  return [...new Set(values)].sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
}
function filteredExecutionItems(expectedType, row) {
  return executionItemsOfType(expectedType).filter(item => ["moc", "pressure_rating", "diameter"].every(key => !row[key] || String(item[key] || "") === String(row[key])));
}
function resetExecutionItemAfterAttribute(row, itemField, changedField) {
  const fields = ["moc", "pressure_rating", "diameter"];
  const changedIndex = fields.indexOf(changedField);
  fields.slice(changedIndex + 1).forEach(field => { row[field] = ""; });
  row[itemField] = "";
  row.uom = "";
  row.current_stock = 0;
}
function stockWarehouses() {
  if (isTransfer.value) return [form.value.source_warehouse, form.value.target_warehouse];
  const assignment = (options.value.contractors || []).find(row => row.name === form.value.contractor_assignment);
  return [assignment?.contractor_warehouse || "", ""];
}
async function refreshRowStock(row, field = "item_code") {
  const itemCode = row[field];
  if (!itemCode) return;
  const [source, target] = stockWarehouses();
  try {
    row.source_stock = source ? await call("cmr_pipe_laying_master.api.entries.get_warehouse_stock", { item_code: itemCode, warehouse: source }) : 0;
    row.target_stock = target ? await call("cmr_pipe_laying_master.api.entries.get_warehouse_stock", { item_code: itemCode, warehouse: target }) : 0;
    if (!isTransfer.value) row.current_stock = row.source_stock;
  } catch (e) { row.source_stock = 0; row.target_stock = 0; row.current_stock = 0; }
}
function refreshAllStocks() {
  (form.value.items || []).forEach(row => refreshRowStock(row));
  (form.value.segments || []).forEach(row => refreshRowStock(row, "pipe_item"));
  (form.value.fittings || []).forEach(row => refreshRowStock(row));
  if (form.value.valve_item) refreshRowStock(form.value, "valve_item");
}

function selectAttachment(field, label) {
  if (!window.frappe?.ui?.FileUploader) { error.value = "Attachment uploader is unavailable. Please refresh and try again."; return; }
  new window.frappe.ui.FileUploader({ allow_multiple: false, is_private: 1, on_success(file) { form.value[field] = file.file_url; window.frappe.show_alert({ message: `${label} attached`, indicator: "green" }, 5); } });
}
function attachmentFileName(path, fallback) {
  if (!path) return `No ${fallback.toLowerCase()} attached`;
  const value = String(path).split("?")[0].split("/").pop() || fallback;
  try { return decodeURIComponent(value); } catch (e) { return value; }
}
function addBreakup() {
  if (!breakupItems.value.length) {
    error.value = "Please select a Pipe item in Material Items first to use the Pipe / Roll breakup.";
    return;
  }
  error.value = "";
  const row = blankBreakup();
  if (breakupItems.value.length === 1) row.item_code = breakupItems.value[0].item_code;
  form.value.quantity_breakup.push(row);
}
function recalculateBreakup(row) { row.total_length = roundedMeasurement(measurementNumber(row.nos) * measurementNumber(row.length)); }
function captureRowGps(row) {
  if (!navigator.geolocation) { error.value = "GPS location is unavailable in this browser or device."; return; }
  navigator.geolocation.getCurrentPosition(position => { row.gps_latitude = Number(position.coords.latitude.toFixed(6)); row.gps_longitude = Number(position.coords.longitude.toFixed(6)); window.frappe.show_alert({ message: "Fitting GPS captured", indicator: "green" }, 5); }, () => { error.value = "Fitting GPS could not be captured. Check location permission."; }, { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 });
}
function openMaster(pageKey) { emit("create-master", pageKey); }
function addRow(table, factory) { form.value[table].push(factory()); }
function removeRow(table, index) { if (form.value[table].length > 1 || ["fittings", "quantity_breakup"].includes(table)) form.value[table].splice(index, 1); }
function amount(row) { return (Number(row.qty) || 0) * (Number(row.rate) || 0); }
function measurementNumber(value) { const number = Number(value); return Number.isFinite(number) ? number : 0; }
function roundedMeasurement(value) { return Math.round((measurementNumber(value) + Number.EPSILON) * 1000) / 1000; }
function measurementTotal(rows, field) { return roundedMeasurement((rows || []).reduce((total, row) => total + measurementNumber(row[field]), 0)); }
function validDimensions(values) { return values.every(value => Number.isFinite(Number(value)) && Number(value) >= 0); }
function recalculateSegment(row) {
  if (!validDimensions([row.chainage_from, row.chainage_to])) { row.chainage_length = 0; return; }
  row.chainage_length = roundedMeasurement(Math.abs(Number(row.chainage_to) - Number(row.chainage_from)));
}
function recalculateExcavation(row) {
  if (!validDimensions([row.length, row.width, row.calculated_depth, row.actual_depth])) { row.calculated_qty = 0; row.actual_qty = 0; return; }
  row.calculated_qty = roundedMeasurement(Number(row.length) * Number(row.width) * Number(row.calculated_depth));
  row.actual_qty = roundedMeasurement(Number(row.length) * Number(row.width) * Number(row.actual_depth));
}
function recalculateRefill(row) {
  if (!validDimensions([row.length, row.width, row.depth])) { row.quantity = 0; return; }
  row.quantity = roundedMeasurement(Number(row.length) * Number(row.width) * Number(row.depth));
}
function recalculatePipeForm() {
  if (props.pageKey !== "pipe-laying" || !props.hierarchyEnabled) return;
  (form.value.segments || []).forEach(recalculateSegment);
  (form.value.excavation_details || []).forEach(recalculateExcavation);
  (form.value.refill_details || []).forEach(recalculateRefill);
}
function displayDoctype(value) { return String(value || "").replace(/^CMR\s+/, ""); }
function captureGps() {
  gpsMessage.value = "";
  gpsMessageType.value = "";
  if (!navigator.geolocation) {
    gpsMessage.value = "GPS location is unavailable in this browser or device.";
    gpsMessageType.value = "error";
    return;
  }

  gpsCapturing.value = true;
  navigator.geolocation.getCurrentPosition(
    position => {
      form.value.gps_latitude = Number(position.coords.latitude.toFixed(6));
      form.value.gps_longitude = Number(position.coords.longitude.toFixed(6));
      form.value.gps_accuracy = gpsAccuracy.value = Number.isFinite(position.coords.accuracy)
        ? Number(position.coords.accuracy.toFixed(2))
        : null;
      gpsMessage.value = "GPS location captured successfully.";
      gpsMessageType.value = "success";
      gpsCapturing.value = false;
    },
    locationError => {
      const messages = {
        1: "Location permission was denied. Please allow location access and try again.",
        2: "GPS location is currently unavailable. Please try again.",
        3: "GPS request timed out. Please try again.",
      };
      gpsMessage.value = messages[locationError.code] || "GPS location could not be captured.";
      gpsMessageType.value = "error";
      gpsCapturing.value = false;
    },
    { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 },
  );
}
function hasRestorationGps(target) {
  const latitude = form.value[`gps_latitude_${target}`];
  const longitude = form.value[`gps_longitude_${target}`];
  return latitude !== null && latitude !== "" && latitude !== undefined && longitude !== null && longitude !== "" && longitude !== undefined;
}
function restorationGpsButtonLabel(target) { return hasRestorationGps(target) ? `Refresh ${target === "from" ? "From" : "To"} Location` : `Capture ${target === "from" ? "From" : "To"} Location`; }
function captureRestorationGps(target) {
  gpsMessage.value = "";
  gpsMessageType.value = "";
  if (!navigator.geolocation) {
    gpsMessage.value = "GPS location is unavailable in this browser or device.";
    gpsMessageType.value = "error";
    return;
  }

  restorationGpsTarget.value = target;
  navigator.geolocation.getCurrentPosition(
    position => {
      form.value[`gps_latitude_${target}`] = Number(position.coords.latitude.toFixed(6));
      form.value[`gps_longitude_${target}`] = Number(position.coords.longitude.toFixed(6));
      gpsMessage.value = `${target === "from" ? "From" : "To"} GPS location captured successfully.`;
      gpsMessageType.value = "success";
      restorationGpsTarget.value = "";
    },
    locationError => {
      const messages = {
        1: "Location permission was denied. Please allow location access and try again.",
        2: "GPS location is currently unavailable. Please try again.",
        3: "GPS request timed out. Please try again.",
      };
      gpsMessage.value = messages[locationError.code] || "GPS location could not be captured.";
      gpsMessageType.value = "error";
      restorationGpsTarget.value = "";
    },
    { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 },
  );
}
function keepNonNegative(field) { if (Number(form.value[field]) < 0) form.value[field] = 0; }
function digitsOnly(field) { form.value[field] = (form.value[field] || "").replace(/\D/g, ""); }
function concreteQtyNumber(grade) { return roundedMeasurement((Number(form.value[`${grade}_length`]) || 0) * (Number(form.value.pipe_width) || 0) * (Number(form.value[`${grade}_depth`]) || 0)); }
function concreteQty(grade) { return concreteQtyNumber(grade).toFixed(3); }
function validateRestorationForm() {
  if (!isRaisoniRestoration.value) return true;
  const dimensionFields = ["pipe_length", "pipe_width", "dismantling_length", "dismantling_depth", "m15_length", "m15_depth", "m20_length", "m20_depth", "m30_length", "m30_depth"];
  if (!validDimensions(dimensionFields.map(field => form.value[field]))) {
    error.value = "Restoration dimensions must be numeric and cannot be negative.";
    return false;
  }
  if (Number(form.value.pipe_length) <= 0 || Number(form.value.pipe_width) <= 0) {
    error.value = "Restoration Length and Width must be greater than zero.";
    return false;
  }
  if (Number(form.value.dismantling_length) > Number(form.value.pipe_length)) {
    error.value = "Dismantling Length cannot exceed Restoration Length.";
    return false;
  }
  for (const grade of ["m15", "m20", "m30"]) {
    if (Number(form.value[`${grade}_length`]) > Number(form.value.pipe_length)) {
      error.value = `${grade.toUpperCase()} Length cannot exceed Restoration Length.`;
      return false;
    }
  }
  return true;
}
function confirmAction(message) {
  return new Promise(resolve => {
    if (window.frappe?.confirm) window.frappe.confirm(message, () => resolve(true), () => resolve(false));
    else resolve(window.confirm(message));
  });
}
function printDocument() {
  if (!documentInfo.value) return;
  const query = new URLSearchParams({ doctype: documentInfo.value.doctype, name: activeRecordName.value, format: "Standard", no_letterhead: "0", trigger_print: "1" });
  window.open(`/printview?${query.toString()}`, "_blank", "noopener");
}
async function runAction(action) {
  const prompts = { delete: "Delete this Draft document permanently?", cancel: "Cancel this Submitted document? This will reverse its ERP effects.", close: "Close this Purchase Receipt?", reopen: "Reopen this Purchase Receipt?" };
  if (prompts[action] && !await confirmAction(prompts[action])) return;
  saving.value = true; error.value = ""; success.value = null;
  try {
    const result = await call("cmr_pipe_laying_master.api.entries.run_entry_action", { entry_type: props.pageKey, record_name: activeRecordName.value, action });
    if (result.deleted) {
      window.frappe.show_alert({ message: `${result.name} deleted`, indicator: "green" }, 6);
      emit("saved", result);
      return;
    }
    if (["amend", "duplicate"].includes(action)) activeRecordName.value = result.name;
    await loadDocument();
    window.frappe.show_alert({ message: `${activeRecordName.value} ${action} completed`, indicator: "green" }, 6);
  } catch (e) { error.value = `Document action '${action}' could not be completed. Please check ERP status, links and permissions.`; }
  finally { saving.value = false; }
}

async function save(action) {
  error.value = ""; success.value = null;
  if (action === "submit" && isRaisoniValve.value && !hasGpsLocation.value) {
    error.value = "Please capture GPS location before submitting.";
    return;
  }
  if (!validateRestorationForm()) return;
  saving.value = true;
  try {
    recalculatePipeForm();
    if (isRaisoniRestoration.value) {
      form.value.dismantling_quantity = dismantlingQuantity.value;
      form.value.total_concrete_quantity = totalConcreteQuantity.value;
      for (const grade of ["m15", "m20", "m30"]) form.value[`${grade}_quantity`] = concreteQtyNumber(grade);
    }
    if (isRaisoniValve.value) form.value.total_fitting_qty = totalFittingQty.value;
    success.value = await call("cmr_pipe_laying_master.api.entries.save_entry", { entry_type: props.pageKey, payload: JSON.stringify(form.value), action, record_name: activeRecordName.value });
    window.frappe.show_alert({ message: `${success.value.name} ${isEditing.value ? "updated" : "saved"} successfully`, indicator: "green" }, 7);
    emit("saved", success.value);
  } catch (e) {
    error.value = "Entry could not be saved. Please check required fields, stock, linked documents and permissions.";
  } finally { saving.value = false; }
}

resetForm();
activeRecordName.value = props.recordName || "";
onMounted(loadOptions);
</script>
<template>
  <section class="cmr-modern-form">
    <div class="cmr-form-toolbar">
      <div>
        <button class="cmr-back-link" type="button" @click="emit('close')">← Back</button>
        <h2>{{ formHeading }}</h2>
        <p class="cmr-backend-document-label"><b v-if="activeRecordName">{{ activeRecordName }}</b><span v-if="activeRecordName"> • </span>Portal entry - ERPNext backend document</p>
      </div>
      <div class="cmr-form-actions">
        <template v-if="!documentInfo || documentInfo.docstatus === 0">
          <button v-if="documentInfo?.can_delete" class="cmr-button danger" type="button" :disabled="saving" @click="runAction('delete')">Delete</button>
          <button v-if="!documentInfo || documentInfo.can_write" class="cmr-button" type="button" :disabled="saving" @click="save('draft')">Save Draft</button>
          <button v-if="!documentInfo || documentInfo.can_submit" class="cmr-button primary" type="button" :disabled="saving" @click="save('submit')">{{ saving ? 'Saving…' : isEditing ? 'Update & Submit' : submitLabel }}</button>
        </template>
        <template v-else>
          <button v-if="pageKey === 'material-inward' && documentInfo.doctype === 'Purchase Receipt' && documentInfo.docstatus === 1 && !documentInfo.is_return && documentInfo.can_create && purchaseReturns?.available_qty > 0" class="cmr-button primary" type="button" :disabled="saving" @click="emit('return-material', activeRecordName)">Return Material</button>
          <button class="cmr-button" type="button" :disabled="saving" @click="printDocument">Print</button>
          <button v-if="documentInfo.can_create" class="cmr-button" type="button" :disabled="saving" @click="runAction('duplicate')">Duplicate</button>
          <button v-if="documentInfo.doctype === 'Purchase Receipt' && documentInfo.docstatus === 1 && documentInfo.can_submit && documentInfo.status !== 'Closed'" class="cmr-button" type="button" :disabled="saving" @click="runAction('close')">Close</button>
          <button v-if="documentInfo.doctype === 'Purchase Receipt' && documentInfo.docstatus === 1 && documentInfo.can_submit && documentInfo.status === 'Closed'" class="cmr-button" type="button" :disabled="saving" @click="runAction('reopen')">Reopen</button>
          <button v-if="documentInfo.docstatus === 1 && documentInfo.can_cancel" class="cmr-button danger" type="button" :disabled="saving" @click="runAction('cancel')">Cancel</button>
          <button v-if="documentInfo.docstatus === 2 && documentInfo.can_create" class="cmr-button primary" type="button" :disabled="saving" @click="runAction('amend')">Amend</button>
        </template>
      </div>
    </div>
    <div class="cmr-native-note"><span>♦</span>This form stays inside Pipe Laying. ERPNext permissions, validations and stock rules run for every action.</div>
    <div v-if="documentInfo" class="cmr-document-state">
      <div><b>{{ documentInfo.name }}</b><small>{{ displayDoctype(documentInfo.doctype) }} • Last updated {{ documentInfo.modified }}</small></div>
      <span class="cmr-status-pill" :class="`status-${documentInfo.docstatus}`">{{ statusLabel }}</span>
      <p v-if="isReadOnly">Submitted and Cancelled documents are read-only, exactly like ERPNext. Use the available lifecycle actions above.</p>
    </div>
    <div v-if="pageKey === 'material-inward' && documentInfo && !documentInfo.is_return && purchaseReturns" class="cmr-return-summary">
      <div><span>Supplier Return Status</span><b>{{ purchaseReturns.status }}</b></div>
      <div><span>Returned Qty</span><b>{{ Number(purchaseReturns.returned_qty || 0).toFixed(3) }}</b></div>
      <div><span>Available Qty</span><b>{{ Number(purchaseReturns.available_qty || 0).toFixed(3) }}</b></div>
      <div v-if="purchaseReturns.returns?.length" class="cmr-return-links"><span>Purchase Returns</span><button v-for="row in purchaseReturns.returns" :key="row.name" type="button" @click="emit('edit-return', row.name)">{{ row.name }} · {{ row.docstatus === 0 ? 'Draft' : row.docstatus === 1 ? 'Submitted' : 'Cancelled' }}</button></div>
    </div>
    <div v-if="loading" class="cmr-form-message">Loading form data…</div>
    <div v-if="error" class="cmr-form-message error">{{ error }}</div>
    <div v-if="success" class="cmr-form-message success cmr-document-result"><b>{{ success.name }}</b> backend {{ displayDoctype(success.doctype) }} me successfully save hua. <button type="button" @click="resetForm">Create another</button></div>

    <fieldset v-if="!loading" class="cmr-document-fields" :disabled="isReadOnly">

      <div class="cmr-form-section">
        <div class="cmr-section-title"><span>1</span><div><b>{{ isMaterial ? 'Document Details' : 'Work Information' }}</b><small>Basic reference and project information</small></div></div>
        <div class="cmr-form-grid">
          <label v-if="isRaisoniReferenceEntry"><span>Pipe Measurement *</span><SearchSelect v-model="form.pipe_measurement" :options="filteredMeasurements" secondary-key="project" placeholder="Search submitted measurement..." @change="selectMeasurement" /></label>
          <label><span>Date *</span><input v-model="form[isMaterial ? 'posting_date' : pageKey === 'pipe-laying' ? 'laying_date' : pageKey === 'valves' ? 'installation_date' : 'restoration_date']" type="date" /></label>
          <label><span>Company *</span><SearchSelect v-model="form.company" :options="options.companies" :disabled="isRaisoniReferenceEntry" placeholder="Search company…" /></label>
          <label v-if="pageKey === 'material-inward'"><span>Supplier *</span><SearchSelect v-model="form.supplier" :options="options.suppliers" label-key="supplier_name" placeholder="Search supplier…" create-label="Create a new Supplier" @create="openMaster('master-supplier')" /></label>
          <label><span>Project *</span><SearchSelect v-model="form.project" :options="options.projects" :disabled="isRaisoniReferenceEntry" label-key="project_name" placeholder="Search project…" create-label="Create a new Project" @change="projectChanged" @create="openMaster('master-project')" /></label>
          <label><span>Site *</span><SearchSelect v-model="form.site" :options="filteredSites" :disabled="isRaisoniReferenceEntry" label-key="site_name" secondary-key="project" placeholder="Search site..." create-label="Create a new Site" @change="selectSite" @create="openMaster('master-site')" /></label>

          <template v-if="pageKey === 'material-inward'">
            <label><span>Receiving Store *</span><SearchSelect v-model="form.warehouse" :options="filteredWarehouses" placeholder="Search store…" /></label>
            <label><span>MRN / GRN No</span><input v-model="form.mrn_no" placeholder="MRN reference" /></label>
            <label><span>Supplier Delivery Note</span><input v-model="form.supplier_delivery_note" /></label>
            <label><span>PO Number</span><input v-model="form.po_number" placeholder="Enter PO number…" /></label>
          </template>
          <template v-if="isTransfer">
            <label><span>Contractor Assignment *</span><SearchSelect v-model="form.contractor_assignment" :options="filteredContractors" label-key="contractor" secondary-key="name" placeholder="Search contractor…" create-label="Create a new Contractor Assignment" @change="selectContractor" @create="openMaster('master-contractor')" /></label>
            <label><span>From Store *</span><SearchSelect v-model="form.source_warehouse" :options="filteredWarehouses" placeholder="Search source store…" /></label>
            <label><span>To Store *</span><SearchSelect v-model="form.target_warehouse" :options="filteredTargetWarehouses" placeholder="Search destination store…" /></label>
            <label><span>Receiver / Handed Over To</span><SearchSelect v-model="form.receiver" :options="options.users" label-key="full_name" placeholder="Search receiver…" /></label>
          </template>
          <template v-if="pageKey === 'pipe-laying'">
            <template v-if="hierarchyEnabled">
              <label><span>Zone *</span><SearchSelect v-model="form.zone" :options="filteredZones" label-key="zone_name" secondary-key="site" placeholder="Search zone..." create-label="Create a new Zone" @change="zoneChanged" @create="openMaster('master-zone')" /></label>
              <label><span>Village *</span><SearchSelect v-model="form.village" :options="filteredVillages" label-key="village_name" secondary-key="zone" placeholder="Search village..." create-label="Create a new Village" @create="openMaster('master-village')" /></label>
            </template>
            <template v-else><label><span>Zone *</span><input v-model="form.zone" /></label><label><span>Village *</span><input v-model="form.village" /></label></template>
            <label><span>Work Type *</span><select v-model="form.type_of_work"><option v-for="value in selectOptions('type_of_work', ['Raw Water Pipe Laying','Clear Water Pipe Laying','Distribution Pipe Laying'])" :key="value">{{ value }}</option></select></label>
            <label><span>Laying Mode</span><select v-model="form.laying_mode"><option v-for="value in selectOptions('laying_mode', ['Single','Multiple'])" :key="value">{{ value }}</option></select></label>
            <label><span>Trench Method</span><select v-model="form.trench_method"><option v-for="value in selectOptions('trench_method', ['Open Trench','Trenchless','Above Ground','Other'])" :key="value">{{ value }}</option></select></label>
            <label><span>Section Incharge *</span><SearchSelect v-model="form.section_incharge" :options="options.users" label-key="full_name" placeholder="Search site incharge…" /></label>
            <label><span>Contractor Assignment *</span><SearchSelect v-model="form.contractor_assignment" :options="filteredContractors" label-key="contractor" secondary-key="name" placeholder="Search contractor…" create-label="Create a new Contractor Assignment" @change="selectContractor" @create="openMaster('master-contractor')" /></label>
            <label><span>Trench Width (m) *</span><input v-model.number="form.pipe_width" type="number" :min="hierarchyEnabled ? 0.001 : null" step="0.001" @input="keepNonNegative('pipe_width')" /></label>
          </template>
          <template v-if="pageKey === 'valves' || pageKey === 'restoration'">
            <template v-if="isRaisoniReferenceEntry">
              <label><span>Zone *</span><SearchSelect v-model="form.zone" :options="options.zones" label-key="zone_name" secondary-key="site" disabled /></label>
              <label><span>Village *</span><SearchSelect v-model="form.village" :options="options.villages" label-key="village_name" secondary-key="zone" disabled /></label>
              <label><span>Pipe No / Segment *</span><SearchSelect v-model="form.pipe_no" :options="measurementSegments" value-key="pipe_no" label-key="pipe_no" secondary-key="pipe_item" :placeholder="loadingSegments ? 'Loading segments...' : 'Search measurement segment...'" :disabled="!form.pipe_measurement || loadingSegments" /></label>
              <label><span>Contractor Assignment *</span><SearchSelect v-model="form.contractor_assignment" :options="filteredContractors" label-key="contractor" secondary-key="name" disabled /></label>
            </template>
            <template v-else>
              <template v-if="hierarchyEnabled">
                <label><span>Zone *</span><SearchSelect v-model="form.zone" :options="filteredZones" label-key="zone_name" secondary-key="site" placeholder="Search zone..." create-label="Create a new Zone" @change="zoneChanged" @create="openMaster('master-zone')" /></label>
                <label><span>Village *</span><SearchSelect v-model="form.village" :options="filteredVillages" label-key="village_name" secondary-key="zone" placeholder="Search village..." create-label="Create a new Village" @change="villageChanged" @create="openMaster('master-village')" /></label>
              </template>
              <template v-else><label><span>Zone *</span><input v-model="form.zone" /></label><label><span>Village *</span><input v-model="form.village" /></label></template>
              <label><span>Pipe Measurement *</span><SearchSelect v-model="form.pipe_measurement" :options="filteredMeasurements" secondary-key="project" placeholder="Search submitted measurement…" @change="selectMeasurement" /></label>
              <label><span>Pipe No *</span><input v-model="form.pipe_no" placeholder="Pipe/segment number" /></label>
              <label><span>Contractor Assignment *</span><SearchSelect v-model="form.contractor_assignment" :options="filteredContractors" label-key="contractor" secondary-key="name" placeholder="Search contractor…" create-label="Create a new Contractor Assignment" @change="selectContractor" @create="openMaster('master-contractor')" /></label>
            </template>
          </template>
        </div>
      </div>

      <div v-if="pageKey === 'material-inward'" class="cmr-form-section">
        <div class="cmr-section-title"><span>2</span><div><b>Transport & Invoice</b><small>Vehicle, driver and invoice tracking</small></div></div>
        <div class="cmr-form-grid">
          <label><span>Vehicle Type</span><select v-model="form.vehicle_type"><option v-for="value in selectOptions('vehicle_type', ['Truck','Trailer','Tempo','Pickup','Other'])" :key="value">{{ value }}</option></select></label>
          <label><span>Vehicle No</span><input v-model="form.vehicle_no" /></label>
          <label><span>Transporter Name</span><input v-model="form.transporter_name" /></label>
          <label><span>Transport Cost</span><input v-model.number="form.transport_cost" type="number" min="0" step="0.01" @input="keepNonNegative('transport_cost')" /></label>
          <label><span>Driver / Brought By</span><input v-model="form.driver_name" /></label><label><span>Driver Mobile</span><input v-model="form.driver_mobile" type="tel" inputmode="numeric" @input="digitsOnly('driver_mobile')" /></label><label><span>LR No</span><input v-model="form.lr_no" /></label>
          <label><span>Invoice No</span><input v-model="form.invoice_no" /></label><label><span>Invoice Date</span><input v-model="form.invoice_date" type="date" /></label>
          <label><span>Invoice Status</span><select v-model="form.invoice_status"><option v-for="value in selectOptions('invoice_status', ['Pending','Received','Verified','Paid'])" :key="value">{{ value }}</option></select></label>
          <div class="cmr-attachment-field">
            <span>Attachments</span>
            <div class="cmr-attachment-actions">
              <div v-for="attachment in attachmentFields" :key="attachment.field" class="cmr-attachment-item">
                <div class="cmr-attachment-copy">
                  <b>{{ attachment.label }}</b>
                  <a v-if="form[attachment.field]" :href="form[attachment.field]" target="_blank" rel="noopener noreferrer" :title="`Open ${attachment.label} in a new tab`">{{ attachmentFileName(form[attachment.field], attachment.label) }} ↗</a>
                  <small v-else>{{ attachmentFileName('', attachment.label) }}</small>
                </div>
                <button class="cmr-button" type="button" @click="selectAttachment(attachment.field, attachment.label)">{{ form[attachment.field] ? 'Change' : 'Attach' }}</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="isMaterial" class="cmr-form-section">
        <div class="cmr-section-title"><span>{{ pageKey === 'material-inward' ? 3 : 2 }}</span><div><b>Material Items</b><small>Stock items and quantities</small></div><button class="cmr-button" type="button" @click="addRow('items', blankItem)">+ Add Item</button></div>
        <div class="cmr-line-table cmr-material-items-table"><table><thead><tr><th>Type</th><th>Item *</th><th>MOC</th><th>Class</th><th>Size</th><th>Qty *</th><th v-if="pageKey === 'material-inward'">Rate</th><th>UOM</th><th v-if="isTransfer">Source Stock</th><th v-if="isTransfer">Receiver Stock</th><th v-if="pageKey === 'material-inward'">Classify</th><th v-if="pageKey === 'material-inward'">Amount</th><th></th></tr></thead><tbody><tr v-for="(row, i) in form.items" :key="i">
          <td data-label="Type"><select v-model="row.material_type" @change="resetItemAfterAttribute(row)"><option value="">All</option><option v-for="value in attributeValues('material_type',row)" :key="value">{{ value }}</option></select></td>
          <td data-label="Item *"><SearchSelect v-model="row.item_code" :options="filteredItems(row)" value-key="item_code" label-key="item_name" secondary-key="item_code" placeholder="Search item…" create-label="Create a new Item" @change="itemChanged(row)" @create="openMaster('master-material')" /></td>
          <td data-label="MOC"><select v-model="row.moc" :disabled="!!row.item_code" @change="resetItemAfterAttribute(row)"><option value="">All</option><option v-for="value in attributeValues('moc',row,['material_type'])" :key="value">{{ value }}</option></select></td>
          <td data-label="Class"><select v-model="row.pressure_rating" :disabled="!!row.item_code" @change="resetItemAfterAttribute(row)"><option value="">All</option><option v-for="value in attributeValues('pressure_rating',row,['material_type','moc'])" :key="value">{{ value }}</option></select></td>
          <td data-label="Size"><select v-model="row.diameter" :disabled="!!row.item_code" @change="resetItemAfterAttribute(row)"><option value="">All</option><option v-for="value in attributeValues('diameter',row,['material_type','moc','pressure_rating'])" :key="value" :value="value">{{ value }}</option></select></td>
          <td data-label="Qty *"><input v-model.number="row.qty" type="number" min="0.001" step="0.001" /></td><td v-if="pageKey === 'material-inward'" data-label="Rate"><input v-model.number="row.rate" type="number" min="0" step="0.01" /></td><td data-label="UOM"><input v-model="row.uom" readonly /></td>
          <td v-if="isTransfer" data-label="Source Stock">{{ Number(row.source_stock || 0).toFixed(3) }}</td><td v-if="isTransfer" data-label="Receiver Stock">{{ Number(row.target_stock || 0).toFixed(3) }}</td>
          <td v-if="pageKey === 'material-inward'" data-label="Classify"><select v-model="row.consumable_type"><option v-for="value in selectOptions('consumable_type', ['Consumable','Non-Consumable'])" :key="value">{{ value }}</option></select></td><td v-if="pageKey === 'material-inward'" data-label="Amount">{{ amount(row).toFixed(2) }}</td><td><button class="cmr-remove" type="button" @click="removeRow('items', i)">×</button></td>
        </tr></tbody></table></div>
        <div class="cmr-section-summary"><span>Total Quantity</span><strong>{{ totalMaterialQuantity.toFixed(3) }}</strong></div>
        <template v-if="pageKey === 'material-inward'">
          <div class="cmr-section-summary"><span>Total Supply Cost</span><strong>{{ totalSupplyCost.toFixed(2) }}</strong><span>Transport</span><strong>{{ Number(form.transport_cost || 0).toFixed(2) }}</strong><span>Final Total</span><strong>{{ finalMaterialTotal.toFixed(2) }}</strong></div>
          <div class="cmr-section-title compact"><div><b>Pipe / Roll Quantity Breakup</b><small>Only selected Material Items classified as Pipe appear here. Nos × Length = Total Length.</small></div><button class="cmr-button" type="button" @click="addBreakup">+ Add Breakup</button></div>
          <div v-if="!breakupItems.length" class="cmr-empty-inline">Select a Pipe item in Material Items first; it will then be available in this breakup.</div>
          <div v-if="form.quantity_breakup.length" class="cmr-line-table"><table><thead><tr><th>Pipe / Roll</th><th>Nos</th><th>Length</th><th>Total Length</th><th></th></tr></thead><tbody><tr v-for="(row,i) in form.quantity_breakup" :key="i"><td data-label="Pipe / Roll"><SearchSelect v-model="row.item_code" :options="breakupItems" value-key="item_code" label-key="item_code" /></td><td data-label="Nos"><input v-model.number="row.nos" type="number" min="0.001" step="0.001" @input="recalculateBreakup(row)" /></td><td data-label="Length"><input v-model.number="row.length" type="number" min="0.001" step="0.001" @input="recalculateBreakup(row)" /></td><td data-label="Total Length"><input :value="Number(row.total_length || 0).toFixed(3)" readonly /></td><td><button class="cmr-remove" type="button" @click="removeRow('quantity_breakup',i)">×</button></td></tr></tbody></table></div>
        </template>
      </div>

      <template v-if="pageKey === 'pipe-laying'">
        <div class="cmr-form-section">
          <div class="cmr-section-title"><span>2</span><div><b>Pipe Segments</b><small>Chainage and actual laying measurement</small></div><button class="cmr-button" type="button" @click="addRow('segments', blankSegment)">+ Add Segment</button></div>
          <div class="cmr-line-table"><table><thead><tr><th>Pipe No *</th><template v-if="hierarchyEnabled"><th>Type</th><th class="cmr-col-wide">Pipe Item *</th><th>MOC</th><th>Class</th><th>Size</th></template><th v-else>Pipe Item *</th><th>Start Node</th><th>End Node</th><th>From</th><th>To</th><th v-if="hierarchyEnabled">Chainage Length</th><th>Actual Length *</th><template v-if="!hierarchyEnabled"><th>Size</th><th>MOC</th><th>Class</th></template><th>Contractor Stock</th><th></th></tr></thead><tbody><tr v-for="(row,i) in form.segments" :key="i"><td data-label="Pipe No *"><input v-model="row.pipe_no" /></td><template v-if="hierarchyEnabled"><td data-label="Type"><input value="Pipe" readonly /></td><td class="cmr-col-wide" data-label="Pipe Item *"><SearchSelect v-model="row.pipe_item" :options="filteredExecutionItems('Pipe',row)" value-key="item_code" label-key="item_name" secondary-key="item_code" placeholder="Search pipe item…" @change="itemChanged(row,'pipe_item')" /></td><td data-label="MOC"><select v-model="row.moc" @change="resetExecutionItemAfterAttribute(row,'pipe_item','moc')"><option value="">All</option><option v-for="value in executionAttributeValues('Pipe','moc',row)" :key="value">{{ value }}</option></select></td><td data-label="Class"><select v-model="row.pressure_rating" @change="resetExecutionItemAfterAttribute(row,'pipe_item','pressure_rating')"><option value="">All</option><option v-for="value in executionAttributeValues('Pipe','pressure_rating',row,['moc'])" :key="value">{{ value }}</option></select></td><td data-label="Size"><select v-model="row.diameter" @change="resetExecutionItemAfterAttribute(row,'pipe_item','diameter')"><option value="">All</option><option v-for="value in executionAttributeValues('Pipe','diameter',row,['moc','pressure_rating'])" :key="value" :value="value">{{ value }}</option></select></td></template><td v-else data-label="Pipe Item *"><SearchSelect v-model="row.pipe_item" :options="options.items" value-key="item_code" label-key="item_name" secondary-key="item_code" placeholder="Search pipe item…" @change="itemChanged(row,'pipe_item')" /></td><td data-label="Start Node"><input v-model="row.start_node" /></td><td data-label="End Node"><input v-model="row.end_node" /></td><td data-label="From"><input v-model.number="row.chainage_from" type="number" :min="hierarchyEnabled ? 0 : null" step="0.001" @input="recalculateSegment(row)" /></td><td data-label="To"><input v-model.number="row.chainage_to" type="number" :min="hierarchyEnabled ? 0 : null" step="0.001" @input="recalculateSegment(row)" /></td><td v-if="hierarchyEnabled" data-label="Chainage Length"><input :value="Number(row.chainage_length || 0).toFixed(3)" readonly /></td><td data-label="Actual Length *"><input v-model.number="row.actual_length" type="number" :min="hierarchyEnabled ? 0.001 : null" step="0.001" /></td><template v-if="!hierarchyEnabled"><td data-label="Size">{{ row.diameter || '—' }}</td><td data-label="MOC">{{ row.moc || '—' }}</td><td data-label="Class">{{ row.pressure_rating || '—' }}</td></template><td data-label="Contractor Stock">{{ Number(row.current_stock || 0).toFixed(3) }}</td><td><button class="cmr-remove" type="button" @click="removeRow('segments',i)">×</button></td></tr></tbody></table></div>
          <div v-if="hierarchyEnabled" class="cmr-section-summary"><span>Total Pipe Laid Length</span><strong>{{ totalPipeLaidLength.toFixed(3) }} m</strong></div>
        </div>
        <div class="cmr-form-section">
          <div class="cmr-section-title"><span>3</span><div><b>Excavation & Refilling</b><small>Earthwork quantities are recalculated and validated in ERPNext</small></div></div>
          <h4>Excavation</h4>
          <div class="cmr-line-table"><table><thead><tr><th>Type</th><th>Length</th><th>Width</th><th>Calculated Depth</th><th>Actual Depth</th><th v-if="hierarchyEnabled">Calculated Qty (m³)</th><th v-if="hierarchyEnabled">Actual Qty (m³)</th><th></th></tr></thead><tbody><tr v-for="(row,i) in form.excavation_details" :key="i"><td data-label="Type"><select v-model="row.excavation_type"><option v-for="value in selectOptions('excavation_type', ['Dismantling Cement Concrete Pavement','Excavation Ordinary Soil','Excavation Hard Rock'])" :key="value">{{ value }}</option></select></td><td data-label="Length"><input v-model.number="row.length" type="number" :min="hierarchyEnabled ? 0 : null" step="0.001" @input="recalculateExcavation(row)" /></td><td data-label="Width"><input v-model.number="row.width" type="number" :min="hierarchyEnabled ? 0 : null" step="0.001" @input="recalculateExcavation(row)" /></td><td data-label="Calculated Depth"><input v-model.number="row.calculated_depth" type="number" :min="hierarchyEnabled ? 0 : null" step="0.001" @input="recalculateExcavation(row)" /></td><td data-label="Actual Depth"><input v-model.number="row.actual_depth" type="number" :min="hierarchyEnabled ? 0 : null" step="0.001" @input="recalculateExcavation(row)" /></td><td v-if="hierarchyEnabled" data-label="Calculated Qty (m³)"><input :value="Number(row.calculated_qty || 0).toFixed(3)" type="number" readonly /></td><td v-if="hierarchyEnabled" data-label="Actual Qty (m³)"><input :value="Number(row.actual_qty || 0).toFixed(3)" type="number" readonly /></td><td><button class="cmr-remove" type="button" @click="removeRow('excavation_details',i)">×</button></td></tr></tbody></table></div>
          <button class="cmr-add-inline" type="button" @click="addRow('excavation_details',blankExcavation)">+ Add excavation</button>
          <div v-if="hierarchyEnabled" class="cmr-section-summary"><span>Total Excavation Qty</span><strong>{{ totalExcavationQty.toFixed(3) }} m³</strong></div>
          <h4>Refilling</h4>
          <div class="cmr-line-table"><table><thead><tr><th>Material</th><th>Length</th><th>Width</th><th>Depth</th><th v-if="hierarchyEnabled">Quantity (m³)</th><th></th></tr></thead><tbody><tr v-for="(row,i) in form.refill_details" :key="i"><td data-label="Material"><select v-model="row.material_type"><option v-for="value in selectOptions('refill_material', ['Murum','Excavated Earth','Metal','Stone Dust','Sand','Good Earth','Other'])" :key="value">{{ value }}</option></select></td><td data-label="Length"><input v-model.number="row.length" type="number" :min="hierarchyEnabled ? 0 : null" step="0.001" @input="recalculateRefill(row)" /></td><td data-label="Width"><input v-model.number="row.width" type="number" :min="hierarchyEnabled ? 0 : null" step="0.001" @input="recalculateRefill(row)" /></td><td data-label="Depth"><input v-model.number="row.depth" type="number" :min="hierarchyEnabled ? 0 : null" step="0.001" @input="recalculateRefill(row)" /></td><td v-if="hierarchyEnabled" data-label="Quantity (m³)"><input :value="Number(row.quantity || 0).toFixed(3)" type="number" readonly /></td><td><button class="cmr-remove" type="button" @click="removeRow('refill_details',i)">×</button></td></tr></tbody></table></div>
          <button class="cmr-add-inline" type="button" @click="addRow('refill_details',blankRefill)">+ Add refill</button>
          <div v-if="hierarchyEnabled" class="cmr-section-summary"><span>Total Refill Qty</span><strong>{{ totalRefillQty.toFixed(3) }} m³</strong></div>
        </div>
        <div class="cmr-form-section">
          <div class="cmr-section-title"><span>4</span><div><b>Fittings & Completion</b><small>Optional fitting consumption and restoration requirement</small></div><button class="cmr-button" type="button" @click="addRow('fittings',blankFitting)">+ Add Fitting</button></div>
          <div v-if="form.fittings.length" class="cmr-line-table"><table><thead><tr><template v-if="hierarchyEnabled"><th>Type</th><th class="cmr-col-wide">Fitting Item *</th><th>MOC</th><th>Class</th><th>Size</th></template><th v-else>Item *</th><th>Qty *</th><th>UOM</th><template v-if="!hierarchyEnabled"><th>Size</th><th>MOC</th><th>Class</th></template><th>Contractor Stock</th><th>Junction</th><th>GPS</th><th></th></tr></thead><tbody><tr v-for="(row,i) in form.fittings" :key="i"><template v-if="hierarchyEnabled"><td data-label="Type"><input value="Fitting" readonly /></td><td class="cmr-col-wide" data-label="Fitting Item *"><SearchSelect v-model="row.item_code" :options="filteredExecutionItems('Fitting',row)" value-key="item_code" label-key="item_name" secondary-key="item_code" placeholder="Search fitting…" @change="itemChanged(row)" /></td><td data-label="MOC"><select v-model="row.moc" :disabled="!!row.item_code" @change="resetExecutionItemAfterAttribute(row,'item_code','moc')"><option value="">All</option><option v-for="value in executionAttributeValues('Fitting','moc',row)" :key="value">{{ value }}</option></select></td><td data-label="Class"><select v-model="row.pressure_rating" :disabled="!!row.item_code" @change="resetExecutionItemAfterAttribute(row,'item_code','pressure_rating')"><option value="">All</option><option v-for="value in executionAttributeValues('Fitting','pressure_rating',row,['moc'])" :key="value">{{ value }}</option></select></td><td data-label="Size"><select v-model="row.diameter" :disabled="!!row.item_code" @change="resetExecutionItemAfterAttribute(row,'item_code','diameter')"><option value="">All</option><option v-for="value in executionAttributeValues('Fitting','diameter',row,['moc','pressure_rating'])" :key="value" :value="value">{{ value }}</option></select></td></template><td v-else data-label="Item *"><SearchSelect v-model="row.item_code" :options="options.items" value-key="item_code" label-key="item_name" secondary-key="item_code" placeholder="Search fitting…" @change="itemChanged(row)" /></td><td data-label="Qty *"><input v-model.number="row.quantity" type="number" :min="hierarchyEnabled ? 0.001 : null" step="0.001" /></td><td data-label="UOM"><input v-model="row.uom" :readonly="hierarchyEnabled" /></td><template v-if="!hierarchyEnabled"><td data-label="Size">{{ row.diameter || '—' }}</td><td data-label="MOC">{{ row.moc || '—' }}</td><td data-label="Class">{{ row.pressure_rating || '—' }}</td></template><td data-label="Contractor Stock">{{ Number(row.current_stock || 0).toFixed(3) }}</td><td data-label="Junction"><input v-model="row.junction_no" /></td><td data-label="GPS"><button class="cmr-button" type="button" @click="captureRowGps(row)">{{ row.gps_latitude != null ? 'Refresh GPS' : 'Capture GPS' }}</button><small v-if="row.gps_latitude != null">{{ row.gps_latitude }}, {{ row.gps_longitude }}</small></td><td><button class="cmr-remove" type="button" @click="removeRow('fittings',i)">×</button></td></tr></tbody></table></div>
          <div v-if="hierarchyEnabled" class="cmr-section-summary"><span>Total Fitting Qty</span><strong>{{ totalFittingQty.toFixed(3) }}</strong></div>
          <div class="cmr-form-grid compact"><label class="cmr-check"><input v-model="form.restoration_required" type="checkbox" :true-value="1" :false-value="0" /><span>Road restoration required</span></label><label><span>End Cap</span><select v-model="form.end_cap"><option v-for="value in selectOptions('end_cap', ['N/A','Yes','No'])" :key="value">{{ value }}</option></select></label></div>
        </div>
      </template>
      <div v-if="pageKey === 'valves'" class="cmr-form-section">
        <div class="cmr-section-title"><span>2</span><div><b>Valve Details</b><small>Valve material, chamber and GPS location</small></div></div>
        <div class="cmr-form-grid">
          <template v-if="hierarchyEnabled"><label><span>Type</span><input value="Valve" readonly /></label>
          <label><span>Valve Item *</span><SearchSelect v-model="form.valve_item" :options="filteredExecutionItems('Valve',form)" value-key="item_code" label-key="item_name" secondary-key="item_code" placeholder="Search valve item…" @change="itemChanged(form,'valve_item')" /></label>
          <label><span>MOC</span><select v-model="form.moc" :disabled="!!form.valve_item" @change="resetExecutionItemAfterAttribute(form,'valve_item','moc')"><option value="">All</option><option v-for="value in executionAttributeValues('Valve','moc',form)" :key="value">{{ value }}</option></select></label><label><span>Class / Specification</span><select v-model="form.pressure_rating" :disabled="!!form.valve_item" @change="resetExecutionItemAfterAttribute(form,'valve_item','pressure_rating')"><option value="">All</option><option v-for="value in executionAttributeValues('Valve','pressure_rating',form,['moc'])" :key="value">{{ value }}</option></select></label><label><span>Size</span><select v-model="form.diameter" :disabled="!!form.valve_item" @change="resetExecutionItemAfterAttribute(form,'valve_item','diameter')"><option value="">All</option><option v-for="value in executionAttributeValues('Valve','diameter',form,['moc','pressure_rating'])" :key="value" :value="value">{{ value }}</option></select></label></template>
          <label v-else><span>Valve Item *</span><SearchSelect v-model="form.valve_item" :options="options.items" value-key="item_code" label-key="item_name" secondary-key="item_code" placeholder="Search valve item…" @change="itemChanged(form,'valve_item')" /></label>
          <label><span>Quantity *</span><input v-model.number="form.quantity" type="number" min="0.001" step="0.001" /></label>
          <label><span>UOM</span><input v-model="form.uom" :readonly="hierarchyEnabled" /></label>
          <template v-if="!hierarchyEnabled"><label><span>MOC</span><input v-model="form.moc" readonly /></label><label><span>Class / Specification</span><input v-model="form.pressure_rating" readonly /></label><label><span>Size</span><input v-model="form.diameter" readonly /></label></template>
          <label><span>Contractor Current Stock</span><input :value="Number(form.current_stock || 0).toFixed(3)" readonly /></label>
          <label><span>Chamber Size *</span><input v-model="form.chamber_size" /></label>
          <label><span>Specific Location</span><input v-model="form.specific_location" /></label>
          <template v-if="!isRaisoniValve">
            <label><span>GPS Latitude *</span><input v-model.number="form.gps_latitude" type="number" step="0.000001" /></label>
            <label><span>GPS Longitude *</span><input v-model.number="form.gps_longitude" type="number" step="0.000001" /></label>
          </template>
        </div>
        <div v-if="isRaisoniValve" class="cmr-gps-panel">
          <div class="cmr-gps-header">
            <div><b>GPS Location</b><small>Location is captured only when you click the button.</small></div>
            <button class="cmr-button primary" type="button" :disabled="gpsCapturing" @click="captureGps">{{ gpsCapturing ? 'Capturing…' : gpsButtonLabel }}</button>
          </div>
          <div class="cmr-form-grid">
            <label><span>GPS Latitude</span><input :value="form.gps_latitude ?? ''" readonly /></label>
            <label><span>GPS Longitude</span><input :value="form.gps_longitude ?? ''" readonly /></label>
            <label><span>GPS Accuracy (m)</span><input :value="gpsAccuracy ?? ''" readonly /></label>
          </div>
          <p v-if="gpsMessage" class="cmr-gps-message" :class="gpsMessageType">{{ gpsMessage }}</p>
          <p class="cmr-gps-help">GPS is optional for Save Draft and required for Save & Submit.</p>
        </div>
        <div class="cmr-section-title compact"><div><b>Valve Fittings</b><small>Optional fitting consumption from contractor stock</small></div><button class="cmr-button" type="button" @click="addRow('fittings',blankFitting)">+ Add Fitting</button></div>
        <div v-if="form.fittings.length" class="cmr-line-table"><table><thead><tr><template v-if="hierarchyEnabled"><th>Type</th><th>MOC</th><th>Class</th><th>Size</th><th>Fitting Item</th></template><th v-else>Item</th><th>Qty</th><th>UOM</th><template v-if="!hierarchyEnabled"><th>Size</th><th>MOC</th><th>Class</th></template><th>Current Stock</th><th></th></tr></thead><tbody><tr v-for="(row,i) in form.fittings" :key="i"><template v-if="hierarchyEnabled"><td data-label="Type"><input value="Fitting" readonly /></td><td data-label="MOC"><select v-model="row.moc" @change="resetExecutionItemAfterAttribute(row,'item_code','moc')"><option value="">All</option><option v-for="value in executionAttributeValues('Fitting','moc',row)" :key="value">{{ value }}</option></select></td><td data-label="Class"><select v-model="row.pressure_rating" @change="resetExecutionItemAfterAttribute(row,'item_code','pressure_rating')"><option value="">All</option><option v-for="value in executionAttributeValues('Fitting','pressure_rating',row,['moc'])" :key="value">{{ value }}</option></select></td><td data-label="Size"><select v-model="row.diameter" @change="resetExecutionItemAfterAttribute(row,'item_code','diameter')"><option value="">All</option><option v-for="value in executionAttributeValues('Fitting','diameter',row,['moc','pressure_rating'])" :key="value" :value="value">{{ value }}</option></select></td><td data-label="Fitting Item"><SearchSelect v-model="row.item_code" :options="filteredExecutionItems('Fitting',row)" value-key="item_code" label-key="item_name" secondary-key="item_code" @change="itemChanged(row)" /></td></template><td v-else data-label="Item"><SearchSelect v-model="row.item_code" :options="options.items" value-key="item_code" label-key="item_name" secondary-key="item_code" @change="itemChanged(row)" /></td><td data-label="Qty"><input v-model.number="row.quantity" type="number" min="0.001" step="0.001" /></td><td data-label="UOM"><input v-model="row.uom" readonly /></td><template v-if="!hierarchyEnabled"><td data-label="Size">{{ row.diameter || '—' }}</td><td data-label="MOC">{{ row.moc || '—' }}</td><td data-label="Class">{{ row.pressure_rating || '—' }}</td></template><td data-label="Current Stock">{{ Number(row.current_stock || 0).toFixed(3) }}</td><td><button class="cmr-remove" type="button" @click="removeRow('fittings',i)">×</button></td></tr></tbody></table></div>
        <div class="cmr-section-summary"><span>Total Fitting Quantity</span><strong>{{ totalFittingQty.toFixed(3) }}</strong></div>      </div>

      <div v-if="pageKey === 'restoration'" class="cmr-form-section">
        <div class="cmr-section-title"><span>2</span><div><b>Restoration Details</b><small>Road dimensions and concrete breakup in meters</small></div></div>
        <div class="cmr-form-grid">
          <label><span>Restoration Length (m) *</span><input v-model.number="form.pipe_length" type="number" min="0.001" step="0.001" @input="keepNonNegative('pipe_length')" /></label>
          <label><span>Restoration Width (m) *</span><input v-model.number="form.pipe_width" type="number" min="0.001" step="0.001" @input="keepNonNegative('pipe_width')" /></label>
          <label><span>Restoration Type *</span><select v-model="form.restoration_type"><option v-for="value in selectOptions('restoration_type', ['CC Road','BT Road','WBM Road','Paver Block','Earthen Road','Other'])" :key="value">{{ value }}</option></select></label>
        </div>
        <div class="cmr-section-title compact"><div><b>Dismantling</b><small>Length × common restoration width × depth</small></div></div>
        <div class="cmr-form-grid"><label><span>Dismantling Length (m)</span><input v-model.number="form.dismantling_length" type="number" min="0" step="0.001" @input="keepNonNegative('dismantling_length')" /></label><label><span>Dismantling Depth (m)</span><input v-model.number="form.dismantling_depth" type="number" min="0" step="0.001" @input="keepNonNegative('dismantling_depth')" /></label><label><span>Dismantling Quantity (m³)</span><input :value="dismantlingQuantity.toFixed(3)" readonly /></label></div>
        <div class="cmr-grade-grid">
          <div v-for="grade in ['m15','m20','m30']" :key="grade">
            <b>{{ grade.toUpperCase() }}</b>
            <label><span>Length (m)</span><input v-model.number="form[`${grade}_length`]" type="number" min="0" step="0.001" @input="keepNonNegative(`${grade}_length`)" /></label>
            <label><span>Depth (m)</span><input v-model.number="form[`${grade}_depth`]" type="number" min="0" step="0.001" @input="keepNonNegative(`${grade}_depth`)" /></label>
            <label><span>Quantity (m³)</span><input :value="concreteQty(grade)" type="number" readonly /></label>
          </div>
        </div>
        <div class="cmr-section-summary"><span>Total Concrete Quantity</span><strong>{{ totalConcreteQuantity.toFixed(3) }} m³</strong></div>

        <div v-if="isRaisoniRestoration" class="cmr-gps-panel">
          <div class="cmr-gps-header">
            <div><b>From Location</b><small>Capture the restoration starting point explicitly.</small></div>
            <button class="cmr-button primary" type="button" :disabled="Boolean(restorationGpsTarget)" @click="captureRestorationGps('from')">{{ restorationGpsTarget === 'from' ? 'Capturing…' : restorationGpsButtonLabel('from') }}</button>
          </div>
          <div class="cmr-form-grid">
            <label><span>From Latitude</span><input :value="form.gps_latitude_from ?? ''" readonly /></label>
            <label><span>From Longitude</span><input :value="form.gps_longitude_from ?? ''" readonly /></label>
          </div>
          <div class="cmr-gps-header secondary">
            <div><b>To Location</b><small>Capture the restoration ending point explicitly.</small></div>
            <button class="cmr-button primary" type="button" :disabled="Boolean(restorationGpsTarget)" @click="captureRestorationGps('to')">{{ restorationGpsTarget === 'to' ? 'Capturing…' : restorationGpsButtonLabel('to') }}</button>
          </div>
          <div class="cmr-form-grid">
            <label><span>To Latitude</span><input :value="form.gps_latitude_to ?? ''" readonly /></label>
            <label><span>To Longitude</span><input :value="form.gps_longitude_to ?? ''" readonly /></label>
          </div>
          <p v-if="gpsMessage" class="cmr-gps-message" :class="gpsMessageType">{{ gpsMessage }}</p>
          <p class="cmr-gps-help">GPS is captured only from these buttons. Existing business rules do not require it for Draft or Submit.</p>
        </div>
        <div v-else class="cmr-form-grid">
          <label><span>From Latitude</span><input v-model.number="form.gps_latitude_from" type="number" /></label>
          <label><span>From Longitude</span><input v-model.number="form.gps_longitude_from" type="number" /></label>
          <label><span>To Latitude</span><input v-model.number="form.gps_latitude_to" type="number" /></label>
          <label><span>To Longitude</span><input v-model.number="form.gps_longitude_to" type="number" /></label>
        </div>
      </div>
      <div class="cmr-form-section"><div class="cmr-section-title"><span>✓</span><div><b>Remarks</b><small>Optional notes for this document</small></div></div><label class="cmr-full-field"><span>Remarks</span><textarea v-model="form.remarks" rows="3" placeholder="Enter remarks or site notes"></textarea></label></div>
    </fieldset>
  </section>
</template>
