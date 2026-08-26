<script setup>
import { computed, onMounted, ref, watch } from "vue";
import "../modern-form.css";
import SearchSelect from "../components/forms/SearchSelect.vue";

const props = defineProps({ pageKey: String, title: String, simpleMasters: Boolean, hierarchyEnabled: { type: Boolean, default: false }, recordName: { type: String, default: "" } });
const emit = defineEmits(["close", "create-master", "saved"]);
const options = ref({});
const form = ref({});
const loading = ref(true);
const saving = ref(false);
const error = ref("");
const success = ref(null);
const isEditing = computed(() => Boolean(props.recordName));
const itemNameTouched = ref(false);
const filteredWarehouses = computed(() => (options.value.warehouses || []).filter(row => !form.value.company || row.company === form.value.company));
const filteredParentWarehouses = computed(() => (options.value.parent_warehouses || []).filter(row => !form.value.company || row.company === form.value.company));
const filteredSites = computed(() => (options.value.sites || []).filter(row => !form.value.project || row.project === form.value.project));
const filteredZones = computed(() => (options.value.zones || []).filter(row => form.value.project && form.value.site && row.project === form.value.project && row.site === form.value.site));

function reset() {
  success.value = null; error.value = ""; itemNameTouched.value = false;
  const simple = {
    "master-project": { project_name: "" },
    "master-site": { site_name: "", project: "" },
  };
  const forms = {
    "master-project": { project_name: "", company: "", expected_start_date: new Date().toISOString().slice(0, 10), expected_end_date: "", notes: "" },
    "master-site": { site_name: "", company: "", project: "", zone: "", village: "", site_incharge: "", default_warehouse: "", address: "" },
    "master-zone": { zone_name: "", project: "", site: "", enabled: 1 },
    "master-village": { village_name: "", project: "", site: "", zone: "", enabled: 1 },
    "master-material": { item_code: "", item_name: "", item_group: "", stock_uom: "Nos", is_stock_item: 1, custom_cmr_material_type: "", custom_cmr_moc: "", custom_cmr_pressure_rating: "", custom_cmr_diameter: "", description: "" },
    "master-contractor": { contractor: "", company: "", project: "", site: "", work_type: "Multiple", contractor_warehouse: "", from_date: new Date().toISOString().slice(0, 10), to_date: "" },
    "master-supplier": { supplier_name: "", supplier_group: "", supplier_type: "Company", mobile_no: "", email_id: "" },
    "master-store": { warehouse_name: "", company: "", parent_warehouse: "" },
    "master-attributes": { attribute_name: "", values: "" },
  };
  form.value = props.simpleMasters && simple[props.pageKey] ? simple[props.pageKey] : (forms[props.pageKey] || {});
}
function call(method, args = {}) { return new Promise((resolve, reject) => window.frappe.call({ method, args, callback: r => resolve(r.message), error: reject })); }
async function load() {
  try {
    options.value = await call("cmr_pipe_laying_master.api.masters.get_master_options");
    if (isEditing.value) {
      form.value = await call("cmr_pipe_laying_master.api.masters.get_master_document", { master_type: props.pageKey, record_name: props.recordName });
    } else if (!form.value.company) {
      form.value.company = options.value.companies?.[0]?.name || "";
    }
  }
  catch (e) { error.value = isEditing.value ? "Could not load the existing record. Please check permissions and try again." : "You do not have permission to manage this ERPNext master."; }
  finally { loading.value = false; }
}
watch(() => form.value.company, company => {
  for (const field of ["contractor_warehouse", "parent_warehouse"]) {
    const rows = field === "parent_warehouse" ? (options.value.parent_warehouses || []) : (options.value.warehouses || []);
    const selected = rows.find(row => row.name === form.value[field]);
    if (selected && company && selected.company !== company) form.value[field] = "";
  }
});
watch(() => form.value.item_code, code => {
  if (props.pageKey === "master-material" && !isEditing.value && !itemNameTouched.value) form.value.item_name = code;
});
function attributeOptions(key, fallback = []) {
  const configured = options.value.item_attributes?.[key] || [];
  return configured.length ? configured : fallback;
}
function selectOptions(key, fallback = []) {
  const configured = options.value.select_options?.[key] || [];
  return configured.length ? configured : fallback;
}
function projectChanged() { form.value.site = ""; form.value.zone = ""; }
function digitsOnly(field) { form.value[field] = (form.value[field] || "").replace(/\D/g, ""); }
function siteChanged() {
  const site = options.value.sites?.find(x => x.name === form.value.site);
  if (props.hierarchyEnabled) form.value.zone = "";
  if (site) { form.value.company = site.company; form.value.project = site.project; }
}
async function save() {
  saving.value = true; error.value = "";
  try {
    success.value = await call("cmr_pipe_laying_master.api.masters.save_master", { master_type: props.pageKey, payload: JSON.stringify(form.value), record_name: props.recordName || "" });
    window.frappe.show_alert({ message: `${success.value.name} ${isEditing.value ? 'updated' : 'created'}`, indicator: "green" }, 6);
    emit("saved", success.value);
  }
  catch (e) { error.value = `Could not ${isEditing.value ? 'update' : 'save'} the master. Please check required values and permissions.`; }
  finally { saving.value = false; }
}
reset(); onMounted(load);
</script>

<template>
  <section class="cmr-modern-form cmr-master-form">
    <div class="cmr-form-toolbar"><div><button class="cmr-back-link" type="button" @click="emit('close')">← Back</button><h2>{{ isEditing ? 'Edit' : 'New' }} {{ title }}</h2><p class="cmr-backend-document-label">Master setup - ERPNext backend</p></div><div class="cmr-form-actions"><button class="cmr-button" type="button" @click="emit('close')">Cancel</button><button class="cmr-button primary" type="button" :disabled="saving" @click="save">{{ saving ? 'Saving…' : isEditing ? 'Update' : 'Save' }}</button></div></div>
    <div class="cmr-native-note"><span>♢</span>This form stays inside Pipe Laying and saves to the connected ERPNext master.</div>
    <div v-if="loading" class="cmr-form-message">Loading master data…</div><div v-if="error" class="cmr-form-message error">{{ error }}</div><div v-if="success" class="cmr-form-message success cmr-document-result"><b>{{ success.name }}</b> successfully {{ isEditing ? 'updated' : 'created' }}.</div>
    <div v-if="!loading" class="cmr-form-section"><div class="cmr-section-title"><span>1</span><div><b>{{ title }} Details</b><small>Required master information</small></div></div><div class="cmr-form-grid">
      <template v-if="pageKey === 'master-project' && simpleMasters"><label><span>Project Name *</span><input v-model="form.project_name" autofocus /></label></template>
      <template v-else-if="pageKey === 'master-project'"><label><span>Project Name *</span><input v-model="form.project_name" /></label><label><span>Company *</span><SearchSelect v-model="form.company" :options="options.companies" placeholder="Search company…" /></label><label><span>Start Date</span><input v-model="form.expected_start_date" type="date" /></label><label><span>Expected End Date</span><input v-model="form.expected_end_date" type="date" /></label></template>
      <template v-if="pageKey === 'master-site' && simpleMasters"><label><span>Site Name *</span><input v-model="form.site_name" autofocus /></label><label v-if="hierarchyEnabled"><span>Project *</span><SearchSelect v-model="form.project" :options="options.projects" label-key="project_name" placeholder="Search project..." create-label="Create a new Project" @create="emit('create-master', 'master-project')" /></label></template>
      <template v-else-if="pageKey === 'master-site'"><label><span>Site Name *</span><input v-model="form.site_name" /></label><label><span>Company *</span><SearchSelect v-model="form.company" :options="options.companies" placeholder="Search company…" /></label><label><span>Project *</span><SearchSelect v-model="form.project" :options="options.projects" label-key="project_name" placeholder="Search project…" create-label="Create a new Project" @create="emit('create-master', 'master-project')" /></label><label><span>Zone / Cluster</span><input v-model="form.zone" /></label><label><span>Village</span><input v-model="form.village" /></label><label><span>Site Incharge</span><SearchSelect v-model="form.site_incharge" :options="options.users" label-key="full_name" placeholder="Search site incharge…" /></label><label><span>Default Store</span><SearchSelect v-model="form.default_warehouse" :options="filteredWarehouses" placeholder="Search store…" /></label></template>
      <template v-if="pageKey === 'master-zone'"><label><span>Zone Name *</span><input v-model="form.zone_name" autofocus /></label><label><span>Project *</span><SearchSelect v-model="form.project" :options="options.projects" label-key="project_name" placeholder="Search project..." @change="projectChanged" /></label><label><span>Site *</span><SearchSelect v-model="form.site" :options="filteredSites" label-key="site_name" secondary-key="project" placeholder="Search site..." @change="siteChanged" /></label><label class="cmr-check"><input v-model="form.enabled" type="checkbox" :true-value="1" :false-value="0" /><span>Enabled</span></label></template>
      <template v-if="pageKey === 'master-village'"><label><span>Village Name *</span><input v-model="form.village_name" autofocus /></label><label><span>Project *</span><SearchSelect v-model="form.project" :options="options.projects" label-key="project_name" placeholder="Search project..." @change="projectChanged" /></label><label><span>Site *</span><SearchSelect v-model="form.site" :options="filteredSites" label-key="site_name" secondary-key="project" placeholder="Search site..." @change="siteChanged" /></label><label><span>Zone *</span><SearchSelect v-model="form.zone" :options="filteredZones" label-key="zone_name" secondary-key="site" placeholder="Search zone..." /></label><label class="cmr-check"><input v-model="form.enabled" type="checkbox" :true-value="1" :false-value="0" /><span>Enabled</span></label></template>
      <template v-if="pageKey === 'master-material'"><label><span>Item Code *</span><input v-model="form.item_code" :disabled="isEditing" /></label><label><span>Item Name *</span><input v-model="form.item_name" @input="itemNameTouched = true" /></label><label><span>Item Group *</span><SearchSelect v-model="form.item_group" :options="options.item_groups" placeholder="Search item group…" /></label><label><span>Stock UOM *</span><SearchSelect v-model="form.stock_uom" :options="options.uoms" placeholder="Search UOM…" /></label><label><span>Material Type</span><select v-model="form.custom_cmr_material_type"><option value="">Select</option><option v-for="value in attributeOptions('material_type',['Pipe','Fitting','Valve','Other'])" :key="value">{{ value }}</option></select></label><label><span>MOC</span><select v-model="form.custom_cmr_moc"><option value="">Select</option><option v-for="value in attributeOptions('moc')" :key="value">{{ value }}</option></select></label><label><span>Class</span><select v-model="form.custom_cmr_pressure_rating"><option value="">Select</option><option v-for="value in attributeOptions('pressure_rating')" :key="value">{{ value }}</option></select></label><label><span>Size</span><select v-model="form.custom_cmr_diameter"><option value="">Select</option><option v-for="value in attributeOptions('diameter')" :key="value" :value="value">{{ value }}</option></select></label><label class="cmr-check"><input v-model="form.is_stock_item" type="checkbox" :true-value="1" :false-value="0" /><span>Maintain Stock</span></label></template>
      <template v-if="pageKey === 'master-supplier'"><label><span>Supplier Name *</span><input v-model="form.supplier_name" /></label><label><span>Supplier Group *</span><SearchSelect v-model="form.supplier_group" :options="options.supplier_groups" placeholder="Search supplier group…" /></label><label><span>Supplier Type</span><select v-model="form.supplier_type"><option v-for="value in selectOptions('supplier_type', ['Company','Individual'])" :key="value">{{ value }}</option></select></label><label><span>Mobile</span><input v-model="form.mobile_no" type="tel" inputmode="numeric" @input="digitsOnly('mobile_no')" /></label><label><span>Email</span><input v-model="form.email_id" type="email" /></label></template>
      <template v-if="pageKey === 'master-store'"><label><span>Store Name *</span><input v-model="form.warehouse_name" /></label><label><span>Company *</span><SearchSelect v-model="form.company" :options="options.companies" placeholder="Search company…" /></label><label><span>Parent Store *</span><SearchSelect v-model="form.parent_warehouse" :options="filteredParentWarehouses" placeholder="Search parent store…" /></label></template>
      <template v-if="pageKey === 'master-contractor'"><label><span>Contractor / Supplier *</span><SearchSelect v-model="form.contractor" :options="options.suppliers" label-key="supplier_name" placeholder="Search contractor…" create-label="Create a new Supplier" @create="emit('create-master', 'master-supplier')" /></label><label><span>Site *</span><SearchSelect v-model="form.site" :options="options.sites" label-key="site_name" secondary-key="project" placeholder="Search site…" @change="siteChanged" /></label><label><span>Company *</span><SearchSelect v-model="form.company" :options="options.companies" placeholder="Search company…" /></label><label><span>Project *</span><SearchSelect v-model="form.project" :options="options.projects" label-key="project_name" placeholder="Search project…" create-label="Create a new Project" @create="emit('create-master', 'master-project')" /></label><label><span>Work Type</span><select v-model="form.work_type"><option v-for="value in selectOptions('contractor_work_type', ['Pipe Laying','Valve Installation','Road Restoration','Multiple'])" :key="value">{{ value }}</option></select></label><label><span>Contractor Store</span><SearchSelect v-model="form.contractor_warehouse" :options="filteredWarehouses" placeholder="Search contractor store…" /></label><label><span>From Date</span><input v-model="form.from_date" type="date" /></label><label><span>To Date</span><input v-model="form.to_date" type="date" /></label></template>
      <template v-if="pageKey === 'master-attributes'"><label><span>Attribute Name *</span><input v-model="form.attribute_name" placeholder="e.g. MOC, Class, Diameter" /></label><label><span>Values *</span><input v-model="form.values" placeholder="HDPE, DI, MS" /></label></template>
    </div><label v-if="pageKey === 'master-material' || (!simpleMasters && ['master-project','master-site'].includes(pageKey))" class="cmr-full-field cmr-master-notes"><span>{{ pageKey === 'master-site' ? 'Address' : pageKey === 'master-material' ? 'Description' : 'Notes' }}</span><textarea v-model="form[pageKey === 'master-site' ? 'address' : pageKey === 'master-material' ? 'description' : 'notes']" rows="3"></textarea></label></div>
  </section>
</template>

<style scoped>.cmr-master-form{max-width:1050px}.cmr-master-notes{margin-top:14px}</style>
