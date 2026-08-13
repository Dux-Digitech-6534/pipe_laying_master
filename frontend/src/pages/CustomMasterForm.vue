<script setup>
import { onMounted, ref } from "vue";
import "../modern-form.css";
import SearchSelect from "../components/forms/SearchSelect.vue";

const props = defineProps({ pageKey: String, title: String, simpleMasters: Boolean });
const emit = defineEmits(["close", "create-master"]);
const options = ref({});
const form = ref({});
const loading = ref(true);
const saving = ref(false);
const error = ref("");
const success = ref(null);

function reset() {
  success.value = null; error.value = "";
  const simple = {
    "master-project": { project_name: "" },
    "master-site": { site_name: "" },
  };
  const forms = {
    "master-project": { project_name: "", company: "", expected_start_date: new Date().toISOString().slice(0, 10), expected_end_date: "", notes: "" },
    "master-site": { site_name: "", company: "", project: "", zone: "", village: "", site_incharge: "", default_warehouse: "", address: "" },
    "master-material": { item_code: "", item_name: "", item_group: "", stock_uom: "Nos", description: "" },
    "master-contractor": { contractor: "", company: "", project: "", site: "", work_type: "Multiple", contractor_warehouse: "", from_date: new Date().toISOString().slice(0, 10), to_date: "" },
    "master-supplier": { supplier_name: "", supplier_group: "", supplier_type: "Company", mobile_no: "", email_id: "" },
    "master-store": { warehouse_name: "", company: "", parent_warehouse: "" },
    "master-attributes": { attribute_name: "", values: "" },
  };
  form.value = props.simpleMasters && simple[props.pageKey] ? simple[props.pageKey] : (forms[props.pageKey] || {});
}
function call(method, args = {}) { return new Promise((resolve, reject) => window.frappe.call({ method, args, callback: r => resolve(r.message), error: reject })); }
async function load() {
  try { options.value = await call("cmr_pipe_laying_master.api.masters.get_master_options"); if (!form.value.company) form.value.company = options.value.companies?.[0]?.name || ""; }
  catch (e) { error.value = "CMR Master Manager permission required."; }
  finally { loading.value = false; }
}
function siteChanged() { const site = options.value.sites?.find(x => x.name === form.value.site); if (site) { form.value.company = site.company; form.value.project = site.project; } }
async function save() {
  saving.value = true; error.value = "";
  try { success.value = await call("cmr_pipe_laying_master.api.masters.save_master", { master_type: props.pageKey, payload: JSON.stringify(form.value) }); window.frappe.show_alert({ message: `${success.value.name} created`, indicator: "green" }, 6); }
  catch (e) { error.value = "Master save nahi hua. Required values aur duplicate name check karein."; }
  finally { saving.value = false; }
}
reset(); onMounted(load);
</script>

<template>
  <section class="cmr-modern-form cmr-master-form">
    <div class="cmr-form-toolbar"><div><button class="cmr-back-link" type="button" @click="emit('close')">← Back</button><h2>New {{ title }}</h2><p>CMR master setup • ERPNext backend</p></div><div class="cmr-form-actions"><button class="cmr-button" type="button" @click="emit('close')">Cancel</button><button class="cmr-button primary" type="button" :disabled="saving" @click="save">{{ saving ? 'Saving…' : 'Save' }}</button></div></div>
    <div class="cmr-native-note"><span>♢</span>This form stays inside CMR Portal and saves to the connected ERPNext master.</div>
    <div v-if="loading" class="cmr-form-message">Loading master data…</div><div v-if="error" class="cmr-form-message error">{{ error }}</div><div v-if="success" class="cmr-form-message success"><b>{{ success.name }}</b> successfully created. <button type="button" @click="reset">Create another</button></div>
    <div v-if="!loading" class="cmr-form-section"><div class="cmr-section-title"><span>1</span><div><b>{{ title }} Details</b><small>Required master information</small></div></div><div class="cmr-form-grid">
      <template v-if="pageKey === 'master-project' && simpleMasters"><label><span>Project Name *</span><input v-model="form.project_name" autofocus /></label></template>
      <template v-else-if="pageKey === 'master-project'"><label><span>Project Name *</span><input v-model="form.project_name" /></label><label><span>Company *</span><SearchSelect v-model="form.company" :options="options.companies" placeholder="Search company…" /></label><label><span>Start Date</span><input v-model="form.expected_start_date" type="date" /></label><label><span>Expected End Date</span><input v-model="form.expected_end_date" type="date" /></label></template>
      <template v-if="pageKey === 'master-site' && simpleMasters"><label><span>Site Name *</span><input v-model="form.site_name" autofocus /></label></template>
      <template v-else-if="pageKey === 'master-site'"><label><span>Site Name *</span><input v-model="form.site_name" /></label><label><span>Company *</span><SearchSelect v-model="form.company" :options="options.companies" placeholder="Search company…" /></label><label><span>Project *</span><SearchSelect v-model="form.project" :options="options.projects" label-key="project_name" placeholder="Search project…" create-label="Create a new Project" @create="emit('create-master', 'master-project')" /></label><label><span>Zone / Cluster</span><input v-model="form.zone" /></label><label><span>Village</span><input v-model="form.village" /></label><label><span>Site Incharge</span><SearchSelect v-model="form.site_incharge" :options="options.users" label-key="full_name" placeholder="Search site incharge…" /></label><label><span>Default Warehouse</span><SearchSelect v-model="form.default_warehouse" :options="options.warehouses" placeholder="Search warehouse…" /></label></template>
      <template v-if="pageKey === 'master-material'"><label><span>Item Code *</span><input v-model="form.item_code" /></label><label><span>Item Name *</span><input v-model="form.item_name" /></label><label><span>Item Group *</span><SearchSelect v-model="form.item_group" :options="options.item_groups" placeholder="Search item group…" /></label><label><span>Stock UOM *</span><SearchSelect v-model="form.stock_uom" :options="options.uoms" placeholder="Search UOM…" /></label></template>
      <template v-if="pageKey === 'master-supplier'"><label><span>Supplier Name *</span><input v-model="form.supplier_name" /></label><label><span>Supplier Group *</span><SearchSelect v-model="form.supplier_group" :options="options.supplier_groups" placeholder="Search supplier group…" /></label><label><span>Supplier Type</span><select v-model="form.supplier_type"><option>Company</option><option>Individual</option></select></label><label><span>Mobile</span><input v-model="form.mobile_no" /></label><label><span>Email</span><input v-model="form.email_id" type="email" /></label></template>
      <template v-if="pageKey === 'master-store'"><label><span>Warehouse Name *</span><input v-model="form.warehouse_name" /></label><label><span>Company *</span><SearchSelect v-model="form.company" :options="options.companies" placeholder="Search company…" /></label><label><span>Parent Warehouse *</span><SearchSelect v-model="form.parent_warehouse" :options="options.parent_warehouses" placeholder="Search parent warehouse…" /></label></template>
      <template v-if="pageKey === 'master-contractor'"><label><span>Contractor / Supplier *</span><SearchSelect v-model="form.contractor" :options="options.suppliers" label-key="supplier_name" placeholder="Search contractor…" create-label="Create a new Supplier" @create="emit('create-master', 'master-supplier')" /></label><label><span>Site *</span><SearchSelect v-model="form.site" :options="options.sites" label-key="site_name" secondary-key="project" placeholder="Search site…" @change="siteChanged" /></label><label><span>Company *</span><SearchSelect v-model="form.company" :options="options.companies" placeholder="Search company…" /></label><label><span>Project *</span><SearchSelect v-model="form.project" :options="options.projects" label-key="project_name" placeholder="Search project…" create-label="Create a new Project" @create="emit('create-master', 'master-project')" /></label><label><span>Work Type</span><select v-model="form.work_type"><option>Pipe Laying</option><option>Valve Installation</option><option>Road Restoration</option><option>Multiple</option></select></label><label><span>Contractor Warehouse</span><SearchSelect v-model="form.contractor_warehouse" :options="options.warehouses" placeholder="Search contractor warehouse…" /></label><label><span>From Date</span><input v-model="form.from_date" type="date" /></label><label><span>To Date</span><input v-model="form.to_date" type="date" /></label></template>
      <template v-if="pageKey === 'master-attributes'"><label><span>Attribute Name *</span><input v-model="form.attribute_name" placeholder="e.g. MOC, Class, Diameter" /></label><label><span>Values *</span><input v-model="form.values" placeholder="HDPE, DI, MS" /></label></template>
    </div><label v-if="pageKey === 'master-material' || (!simpleMasters && ['master-project','master-site'].includes(pageKey))" class="cmr-full-field cmr-master-notes"><span>{{ pageKey === 'master-site' ? 'Address' : pageKey === 'master-material' ? 'Description' : 'Notes' }}</span><textarea v-model="form[pageKey === 'master-site' ? 'address' : pageKey === 'master-material' ? 'description' : 'notes']" rows="3"></textarea></label><div class="cmr-bottom-actions"><button class="cmr-button" type="button" @click="emit('close')">Cancel</button><button class="cmr-button primary" type="button" :disabled="saving" @click="save">Save</button></div></div>
  </section>
</template>

<style scoped>.cmr-master-form{max-width:1050px}.cmr-master-notes{margin-top:14px}</style>
