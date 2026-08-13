<script setup>
import { computed, onMounted, ref, watch } from "vue";
import "../modern-form.css";
import SearchSelect from "../components/forms/SearchSelect.vue";

const props = defineProps({ pageKey: { type: String, required: true }, title: String });
const emit = defineEmits(["close", "saved", "create-master"]);
const today = new Date().toISOString().slice(0, 10);
const loading = ref(true);
const saving = ref(false);
const error = ref("");
const success = ref(null);
const options = ref({ companies: [], projects: [], sites: [], suppliers: [], warehouses: [], items: [], contractors: [], measurements: [], users: [] });
const form = ref({});

const isMaterial = computed(() => ["material-inward", "material-issue", "material-return"].includes(props.pageKey));
const isTransfer = computed(() => ["material-issue", "material-return"].includes(props.pageKey));
const filteredWarehouses = computed(() => options.value.warehouses.filter(row => !form.value.company || row.company === form.value.company));
const submitLabel = computed(() => props.pageKey === "pipe-laying" ? "Send for Approval" : "Save & Submit");

function blankItem() { return { item_code: "", qty: 1, rate: 0, uom: "", material_type: "Pipe", moc: "", pressure_rating: "", diameter: 0, consumable_type: "Consumable" }; }
function blankSegment() { return { pipe_no: "", pipe_item: "", start_node: "", end_node: "", chainage_from: 0, chainage_to: 0, actual_length: 0, diameter: 0, moc: "", pressure_rating: "" }; }
function blankExcavation() { return { excavation_type: "Excavation Ordinary Soil", length: 0, width: 0, calculated_depth: 0, actual_depth: 0 }; }
function blankRefill() { return { material_type: "Sand", length: 0, width: 0, depth: 0 }; }
function blankFitting() { return { item_code: "", quantity: 1, uom: "Nos", junction_no: "", gps_latitude: 0, gps_longitude: 0 }; }

function resetForm() {
  success.value = null; error.value = "";
  if (props.pageKey === "material-inward") form.value = { posting_date: today, company: "", supplier: "", site: "", warehouse: "", supplier_delivery_note: "", mrn_no: "", vehicle_type: "Truck", transport_cost: 0, driver_name: "", driver_mobile: "", lr_no: "", invoice_status: "Pending", remarks: "", items: [blankItem()] };
  else if (isTransfer.value) form.value = { posting_date: today, company: "", project: "", site: "", contractor_assignment: "", source_warehouse: "", target_warehouse: "", remarks: "", items: [blankItem()] };
  else if (props.pageKey === "pipe-laying") form.value = { laying_date: today, company: "", project: "", site: "", zone: "", village: "", type_of_work: "Distribution Pipe Laying", laying_mode: "Single", trench_method: "Open Trench", section_incharge: "", contractor_assignment: "", pipe_width: 0, restoration_required: 1, end_cap: "N/A", remarks: "", segments: [blankSegment()], excavation_details: [blankExcavation()], refill_details: [blankRefill()], fittings: [] };
  else if (props.pageKey === "valves") form.value = { installation_date: today, company: "", project: "", site: "", zone: "", village: "", pipe_measurement: "", pipe_no: "", contractor_assignment: "", valve_item: "", quantity: 1, uom: "Nos", chamber_size: "", specific_location: "", gps_latitude: 0, gps_longitude: 0, remarks: "", fittings: [] };
  else form.value = { restoration_date: today, company: "", project: "", site: "", zone: "", village: "", pipe_measurement: "", pipe_no: "", contractor_assignment: "", pipe_length: 0, pipe_width: 0, restoration_type: "CC Road", m15_length: 0, m15_depth: 0, m20_length: 0, m20_depth: 0, m30_length: 0, m30_depth: 0, gps_latitude_from: 0, gps_longitude_from: 0, gps_latitude_to: 0, gps_longitude_to: 0, remarks: "" };
}

function call(method, args = {}) {
  return new Promise((resolve, reject) => window.frappe.call({ method, args, callback: r => resolve(r.message), error: reject }));
}
async function loadOptions() {
  loading.value = true;
  try {
    options.value = await call("cmr_pipe_laying_master.api.entries.get_entry_options");
    const company = options.value.companies?.[0]?.name || "";
    if (!form.value.company) form.value.company = company;
  } catch (e) { error.value = "Form options could not be loaded. Please check your role permissions."; }
  finally { loading.value = false; }
}
watch(() => form.value.company, company => {
  for (const field of ["warehouse", "source_warehouse", "target_warehouse"]) {
    const selected = options.value.warehouses.find(row => row.name === form.value[field]);
    if (selected && company && selected.company !== company) form.value[field] = "";
  }
});
function selectSite() {
  const site = options.value.sites.find(x => x.name === form.value.site);
  if (!site) return;
  form.value.company = site.company || form.value.company;
  form.value.project = site.project || form.value.project;
  form.value.zone = site.zone || form.value.zone;
  form.value.village = site.village || form.value.village;
  if (props.pageKey === "material-inward" && site.default_warehouse) form.value.warehouse = site.default_warehouse;
  if (props.pageKey === "material-issue" && site.default_warehouse) form.value.source_warehouse = site.default_warehouse;
  if (props.pageKey === "material-return" && site.default_warehouse) form.value.target_warehouse = site.default_warehouse;
}
function selectContractor() {
  const assignment = options.value.contractors.find(x => x.name === form.value.contractor_assignment);
  if (!assignment) return;
  form.value.company = assignment.company || form.value.company;
  form.value.project = assignment.project || form.value.project;
  form.value.site = assignment.site || form.value.site;
  if (props.pageKey === "material-issue") form.value.target_warehouse = assignment.contractor_warehouse || "";
  if (props.pageKey === "material-return") form.value.source_warehouse = assignment.contractor_warehouse || "";
  selectSite();
}
function selectMeasurement() {
  const measurement = options.value.measurements.find(x => x.name === form.value.pipe_measurement);
  if (!measurement) return;
  for (const field of ["company", "project", "site", "zone", "village", "contractor_assignment"]) form.value[field] = measurement[field] || form.value[field];
  selectContractor();
}
function itemChanged(row, field = "item_code") {
  const item = options.value.items.find(x => (x.item_code || x.name) === row[field]);
  if (item) row.uom = item.stock_uom || row.uom;
}
function openMaster(pageKey) { emit("create-master", pageKey); }
function addRow(table, factory) { form.value[table].push(factory()); }
function removeRow(table, index) { if (form.value[table].length > 1 || table === "fittings") form.value[table].splice(index, 1); }
function amount(row) { return (Number(row.qty) || 0) * (Number(row.rate) || 0); }
function keepNonNegative(field) { if (Number(form.value[field]) < 0) form.value[field] = 0; }
function concreteQty(grade) { return ((Number(form.value[`${grade}_length`]) || 0) * (Number(form.value.pipe_width) || 0) * (Number(form.value[`${grade}_depth`]) || 0)).toFixed(3); }

async function save(action) {
  saving.value = true; error.value = ""; success.value = null;
  try {
    success.value = await call("cmr_pipe_laying_master.api.entries.save_entry", { entry_type: props.pageKey, payload: JSON.stringify(form.value), action });
    window.frappe.show_alert({ message: `${success.value.name} saved successfully`, indicator: "green" }, 7);
    emit("saved", success.value);
  } catch (e) {
    error.value = "Entry could not be saved. Required fields, stock and permissions check karein.";
  } finally { saving.value = false; }
}

resetForm();
onMounted(loadOptions);
</script>

<template>
  <section class="cmr-modern-form">
    <div class="cmr-form-toolbar">
      <div><button class="cmr-back-link" type="button" @click="emit('close')">← Back</button><h2>New {{ title }}</h2><p class="cmr-backend-document-label">CMR portal entry • ERPNext backend document</p></div>
      <div class="cmr-form-actions"><button class="cmr-button" type="button" :disabled="saving" @click="save('draft')">Save Draft</button><button class="cmr-button primary" type="button" :disabled="saving" @click="save('submit')">{{ saving ? 'Saving…' : submitLabel }}</button></div>
    </div>
    <div class="cmr-native-note"><span>♢</span>This form stays inside CMR Portal. ERPNext permissions, validations and stock rules run when you save.</div>
    <div v-if="loading" class="cmr-form-message">Loading form data…</div>
    <div v-if="error" class="cmr-form-message error">{{ error }}</div>
    <div v-if="success" class="cmr-form-message success cmr-document-result"><b>{{ success.name }}</b> backend {{ success.doctype }} me successfully save hua. <button type="button" @click="resetForm">Create another</button></div>

    <template v-if="!loading">
      <div class="cmr-form-section">
        <div class="cmr-section-title"><span>1</span><div><b>{{ isMaterial ? 'Document Details' : 'Work Information' }}</b><small>Basic reference and project information</small></div></div>
        <div class="cmr-form-grid">
          <label><span>Date *</span><input v-model="form[isMaterial ? 'posting_date' : pageKey === 'pipe-laying' ? 'laying_date' : pageKey === 'valves' ? 'installation_date' : 'restoration_date']" type="date" /></label>
          <label><span>Company *</span><SearchSelect v-model="form.company" :options="options.companies" placeholder="Search company…" /></label>
          <label v-if="pageKey === 'material-inward'"><span>Supplier *</span><SearchSelect v-model="form.supplier" :options="options.suppliers" label-key="supplier_name" placeholder="Search supplier…" create-label="Create a new Supplier" @create="openMaster('master-supplier')" /></label>
          <label v-if="pageKey !== 'material-inward'"><span>Project *</span><SearchSelect v-model="form.project" :options="options.projects" label-key="project_name" placeholder="Search project…" create-label="Create a new Project" @create="openMaster('master-project')" /></label>
          <label><span>CMR Site *</span><SearchSelect v-model="form.site" :options="options.sites" label-key="site_name" secondary-key="project" placeholder="Search site…" create-label="Create a new Site" @change="selectSite" @create="openMaster('master-site')" /></label>

          <template v-if="pageKey === 'material-inward'">
            <label><span>Receiving Warehouse *</span><SearchSelect v-model="form.warehouse" :options="filteredWarehouses" placeholder="Search warehouse…" /></label>
            <label><span>MRN / GRN No</span><input v-model="form.mrn_no" placeholder="MRN reference" /></label>
            <label><span>Supplier Delivery Note</span><input v-model="form.supplier_delivery_note" /></label>
          </template>
          <template v-if="isTransfer">
            <label><span>Contractor Assignment *</span><SearchSelect v-model="form.contractor_assignment" :options="options.contractors" label-key="contractor" secondary-key="name" placeholder="Search contractor…" create-label="Create a new Contractor Assignment" @change="selectContractor" @create="openMaster('master-contractor')" /></label>
            <label><span>From Warehouse *</span><SearchSelect v-model="form.source_warehouse" :options="filteredWarehouses" placeholder="Search source warehouse…" /></label>
            <label><span>To Warehouse *</span><SearchSelect v-model="form.target_warehouse" :options="filteredWarehouses" placeholder="Search destination warehouse…" /></label>
          </template>
          <template v-if="pageKey === 'pipe-laying'">
            <label><span>Zone *</span><input v-model="form.zone" /></label><label><span>Village *</span><input v-model="form.village" /></label>
            <label><span>Work Type *</span><select v-model="form.type_of_work"><option>Raw Water Pipe Laying</option><option>Clear Water Pipe Laying</option><option>Distribution Pipe Laying</option></select></label>
            <label><span>Laying Mode</span><select v-model="form.laying_mode"><option>Single</option><option>Multiple</option></select></label>
            <label><span>Trench Method</span><select v-model="form.trench_method"><option>Open Trench</option><option>Trenchless</option><option>Above Ground</option><option>Other</option></select></label>
            <label><span>Section Incharge *</span><SearchSelect v-model="form.section_incharge" :options="options.users" label-key="full_name" placeholder="Search site incharge…" /></label>
            <label><span>Contractor Assignment *</span><SearchSelect v-model="form.contractor_assignment" :options="options.contractors" label-key="contractor" secondary-key="name" placeholder="Search contractor…" create-label="Create a new Contractor Assignment" @change="selectContractor" @create="openMaster('master-contractor')" /></label>
            <label><span>Trench Width (m) *</span><input v-model.number="form.pipe_width" type="number" step="0.001" /></label>
          </template>
          <template v-if="pageKey === 'valves' || pageKey === 'restoration'">
            <label><span>Zone *</span><input v-model="form.zone" /></label><label><span>Village *</span><input v-model="form.village" /></label>
            <label><span>Pipe Measurement *</span><SearchSelect v-model="form.pipe_measurement" :options="options.measurements" secondary-key="project" placeholder="Search approved measurement…" @change="selectMeasurement" /></label>
            <label><span>Pipe No *</span><input v-model="form.pipe_no" placeholder="Pipe/segment number" /></label>
            <label><span>Contractor Assignment *</span><SearchSelect v-model="form.contractor_assignment" :options="options.contractors" label-key="contractor" secondary-key="name" placeholder="Search contractor…" create-label="Create a new Contractor Assignment" @change="selectContractor" @create="openMaster('master-contractor')" /></label>
          </template>
        </div>
      </div>

      <div v-if="pageKey === 'material-inward'" class="cmr-form-section">
        <div class="cmr-section-title"><span>2</span><div><b>Transport & Invoice</b><small>Vehicle, driver and invoice tracking</small></div></div>
        <div class="cmr-form-grid"><label><span>Vehicle Type</span><select v-model="form.vehicle_type"><option>Truck</option><option>Trailer</option><option>Tempo</option><option>Pickup</option><option>Other</option></select></label><label><span>Transport Cost</span><input v-model.number="form.transport_cost" type="number" min="0" step="0.01" @input="keepNonNegative('transport_cost')" /></label><label><span>Driver / Brought By</span><input v-model="form.driver_name" /></label><label><span>Driver Mobile</span><input v-model="form.driver_mobile" /></label><label><span>LR No</span><input v-model="form.lr_no" /></label><label><span>Invoice Status</span><select v-model="form.invoice_status"><option>Pending</option><option>Paid</option></select></label></div>
      </div>

      <div v-if="isMaterial" class="cmr-form-section">
        <div class="cmr-section-title"><span>{{ pageKey === 'material-inward' ? 3 : 2 }}</span><div><b>Material Items</b><small>Stock items and quantities</small></div><button class="cmr-button" type="button" @click="addRow('items', blankItem)">+ Add Item</button></div>
        <div class="cmr-line-table"><table><thead><tr><th>Item *</th><th>Qty *</th><th v-if="pageKey === 'material-inward'">Rate</th><th>UOM</th><th v-if="pageKey === 'material-inward'">Type</th><th v-if="pageKey === 'material-inward'">MOC</th><th v-if="pageKey === 'material-inward'">Class</th><th v-if="pageKey === 'material-inward'">Amount</th><th></th></tr></thead><tbody><tr v-for="(row, i) in form.items" :key="i"><td><SearchSelect v-model="row.item_code" :options="options.items" value-key="item_code" label-key="item_name" secondary-key="item_code" placeholder="Search item…" create-label="Create a new Item" @change="itemChanged(row)" @create="openMaster('master-material')" /></td><td><input v-model.number="row.qty" type="number" min="0" step="0.001" /></td><td v-if="pageKey === 'material-inward'"><input v-model.number="row.rate" type="number" min="0" step="0.01" /></td><td><input v-model="row.uom" readonly /></td><td v-if="pageKey === 'material-inward'"><select v-model="row.material_type"><option>Pipe</option><option>Fitting</option><option>Valve</option><option>Consumable</option><option>Other</option></select></td><td v-if="pageKey === 'material-inward'"><input v-model="row.moc" /></td><td v-if="pageKey === 'material-inward'"><input v-model="row.pressure_rating" /></td><td v-if="pageKey === 'material-inward'">{{ amount(row).toFixed(2) }}</td><td><button class="cmr-remove" type="button" @click="removeRow('items', i)">×</button></td></tr></tbody></table></div>
      </div>

      <template v-if="pageKey === 'pipe-laying'">
        <div class="cmr-form-section"><div class="cmr-section-title"><span>2</span><div><b>Pipe Segments</b><small>Chainage and actual laying measurement</small></div><button class="cmr-button" type="button" @click="addRow('segments', blankSegment)">+ Add Segment</button></div><div class="cmr-line-table"><table><thead><tr><th>Pipe No *</th><th>Pipe Item *</th><th>Start Node</th><th>End Node</th><th>From</th><th>To</th><th>Actual Length *</th><th></th></tr></thead><tbody><tr v-for="(row,i) in form.segments" :key="i"><td><input v-model="row.pipe_no" /></td><td><SearchSelect v-model="row.pipe_item" :options="options.items" value-key="item_code" label-key="item_name" secondary-key="item_code" placeholder="Search pipe item…" /></td><td><input v-model="row.start_node" /></td><td><input v-model="row.end_node" /></td><td><input v-model.number="row.chainage_from" type="number" /></td><td><input v-model.number="row.chainage_to" type="number" /></td><td><input v-model.number="row.actual_length" type="number" /></td><td><button class="cmr-remove" type="button" @click="removeRow('segments',i)">×</button></td></tr></tbody></table></div></div>
        <div class="cmr-form-section"><div class="cmr-section-title"><span>3</span><div><b>Excavation & Refilling</b><small>Earthwork quantities are calculated in backend</small></div></div><h4>Excavation</h4><div class="cmr-line-table"><table><thead><tr><th>Type</th><th>Length</th><th>Width</th><th>Calculated Depth</th><th>Actual Depth</th><th></th></tr></thead><tbody><tr v-for="(row,i) in form.excavation_details" :key="i"><td><select v-model="row.excavation_type"><option>Dismantling Cement Concrete Pavement</option><option>Excavation Ordinary Soil</option><option>Excavation Hard Rock</option></select></td><td><input v-model.number="row.length" type="number" /></td><td><input v-model.number="row.width" type="number" /></td><td><input v-model.number="row.calculated_depth" type="number" /></td><td><input v-model.number="row.actual_depth" type="number" /></td><td><button class="cmr-remove" type="button" @click="removeRow('excavation_details',i)">×</button></td></tr></tbody></table></div><button class="cmr-add-inline" type="button" @click="addRow('excavation_details',blankExcavation)">+ Add excavation</button><h4>Refilling</h4><div class="cmr-line-table"><table><thead><tr><th>Material</th><th>Length</th><th>Width</th><th>Depth</th><th></th></tr></thead><tbody><tr v-for="(row,i) in form.refill_details" :key="i"><td><select v-model="row.material_type"><option>Murum</option><option>Excavated Earth</option><option>Metal</option><option>Stone Dust</option><option>Sand</option><option>Good Earth</option><option>Other</option></select></td><td><input v-model.number="row.length" type="number" /></td><td><input v-model.number="row.width" type="number" /></td><td><input v-model.number="row.depth" type="number" /></td><td><button class="cmr-remove" type="button" @click="removeRow('refill_details',i)">×</button></td></tr></tbody></table></div><button class="cmr-add-inline" type="button" @click="addRow('refill_details',blankRefill)">+ Add refill</button></div>
        <div class="cmr-form-section"><div class="cmr-section-title"><span>4</span><div><b>Fittings & Completion</b><small>Optional fitting consumption and restoration requirement</small></div><button class="cmr-button" type="button" @click="addRow('fittings',blankFitting)">+ Add Fitting</button></div><div v-if="form.fittings.length" class="cmr-line-table"><table><thead><tr><th>Item</th><th>Qty</th><th>UOM</th><th>Junction</th><th>Latitude</th><th>Longitude</th><th></th></tr></thead><tbody><tr v-for="(row,i) in form.fittings" :key="i"><td><SearchSelect v-model="row.item_code" :options="options.items" value-key="item_code" label-key="item_name" secondary-key="item_code" placeholder="Search fitting…" @change="itemChanged(row)" /></td><td><input v-model.number="row.quantity" type="number" /></td><td><input v-model="row.uom" /></td><td><input v-model="row.junction_no" /></td><td><input v-model.number="row.gps_latitude" type="number" /></td><td><input v-model.number="row.gps_longitude" type="number" /></td><td><button class="cmr-remove" type="button" @click="removeRow('fittings',i)">×</button></td></tr></tbody></table></div><div class="cmr-form-grid compact"><label class="cmr-check"><input v-model="form.restoration_required" type="checkbox" :true-value="1" :false-value="0" /><span>Road restoration required</span></label><label><span>End Cap</span><select v-model="form.end_cap"><option>N/A</option><option>Yes</option><option>No</option></select></label></div></div>
      </template>

      <div v-if="pageKey === 'valves'" class="cmr-form-section"><div class="cmr-section-title"><span>2</span><div><b>Valve Details</b><small>Valve material, chamber and GPS location</small></div></div><div class="cmr-form-grid"><label><span>Valve Item *</span><SearchSelect v-model="form.valve_item" :options="options.items" value-key="item_code" label-key="item_name" secondary-key="item_code" placeholder="Search valve item…" @change="itemChanged(form,'valve_item')" /></label><label><span>Quantity *</span><input v-model.number="form.quantity" type="number" /></label><label><span>UOM</span><input v-model="form.uom" /></label><label><span>Chamber Size *</span><input v-model="form.chamber_size" /></label><label><span>Specific Location</span><input v-model="form.specific_location" /></label><label><span>GPS Latitude *</span><input v-model.number="form.gps_latitude" type="number" step="0.000001" /></label><label><span>GPS Longitude *</span><input v-model.number="form.gps_longitude" type="number" step="0.000001" /></label></div></div>

      <div v-if="pageKey === 'restoration'" class="cmr-form-section"><div class="cmr-section-title"><span>2</span><div><b>Restoration Details</b><small>Road dimensions and concrete breakup</small></div></div><div class="cmr-form-grid"><label><span>Length (m) *</span><input v-model.number="form.pipe_length" type="number" /></label><label><span>Width (m) *</span><input v-model.number="form.pipe_width" type="number" /></label><label><span>Restoration Type *</span><select v-model="form.restoration_type"><option>CC Road</option><option>BT Road</option><option>WBM Road</option><option>Paver Block</option><option>Earthen Road</option><option>Other</option></select></label></div><div class="cmr-grade-grid"><div v-for="grade in ['m15','m20','m30']" :key="grade"><b>{{ grade.toUpperCase() }}</b><label><span>Length</span><input v-model.number="form[`${grade}_length`]" type="number" /></label><label><span>Depth</span><input v-model.number="form[`${grade}_depth`]" type="number" /></label><strong>{{ concreteQty(grade) }} m³</strong></div></div><div class="cmr-form-grid"><label><span>From Latitude</span><input v-model.number="form.gps_latitude_from" type="number" /></label><label><span>From Longitude</span><input v-model.number="form.gps_longitude_from" type="number" /></label><label><span>To Latitude</span><input v-model.number="form.gps_latitude_to" type="number" /></label><label><span>To Longitude</span><input v-model.number="form.gps_longitude_to" type="number" /></label></div></div>

      <div class="cmr-form-section"><div class="cmr-section-title"><span>✓</span><div><b>Remarks</b><small>Optional notes for this document</small></div></div><label class="cmr-full-field"><span>Remarks</span><textarea v-model="form.remarks" rows="3" placeholder="Enter remarks or site notes"></textarea></label></div>
    </template>
  </section>
</template>
