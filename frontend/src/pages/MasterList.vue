<script setup>
import { computed, onMounted, ref, watch } from "vue";
import PageHeader from "../components/common/PageHeader.vue";

const props = defineProps({ pageKey: String, title: String, description: String, editable: Boolean });
const emit = defineEmits(["create", "edit"]);
const records = ref([]);
const total = ref(0);
const search = ref("");
const loading = ref(false);
const error = ref("");
let searchTimer;

const columns = computed(() => ({
  "master-project": [
    { key: "project_name", label: "Project Name" },
  ],
  "master-site": [
    { key: "site_name", label: "Site Name" },
    ...(props.editable ? [{ key: "project", label: "Project" }] : []),
  ],
  "master-zone": [
    { key: "zone_name", label: "Zone Name" },
    { key: "project", label: "Project" },
    { key: "site", label: "Site" },
    { key: "enabled", label: "Status", enabledStatus: true },
  ],
  "master-village": [
    { key: "village_name", label: "Village Name" },
    { key: "project", label: "Project" },
    { key: "site", label: "Site" },
    { key: "zone", label: "Zone" },
    { key: "enabled", label: "Status", enabledStatus: true },
  ],
  "master-material": [
    { key: "item_code", label: "Item Code" },
    { key: "item_name", label: "Item Name" },
    { key: "item_group", label: "Item Group" },
    { key: "stock_uom", label: "UOM" },
    { key: "disabled", label: "Status", status: true },
  ],
  "master-contractor": [
    { key: "contractor", label: "Contractor" },
    { key: "project", label: "Project" },
    { key: "site", label: "Site" },
    { key: "work_type", label: "Work Type" },
    { key: "active", label: "Status", enabledStatus: true },
  ],
  "master-supplier": [
    { key: "supplier_name", label: "Supplier Name" },
    { key: "supplier_group", label: "Supplier Group" },
    { key: "supplier_type", label: "Supplier Type" },
  ],
  "master-attributes": [
    { key: "attribute_name", label: "Attribute Name" },
    { key: "numeric_values", label: "Value Type", numericStatus: true },
  ],
  "master-store": [
    { key: "warehouse_name", label: "Store Name" },
    { key: "company", label: "Company" },
    { key: "parent_warehouse", label: "Parent Store" },
  ],
}[props.pageKey] || []));

function call(method, args = {}) {
  return new Promise((resolve, reject) => window.frappe.call({ method, args, callback: r => resolve(r.message), error: reject }));
}

function edit(row) {
  if (props.editable) emit("edit", row.name);
}

async function load(append = false) {
  loading.value = true;
  error.value = "";
  try {
    const result = await call("cmr_pipe_laying_master.api.masters.get_master_records", {
      master_type: props.pageKey,
      search: search.value,
      start: append ? records.value.length : 0,
      page_length: 50,
    });
    records.value = append ? [...records.value, ...(result.records || [])] : (result.records || []);
    total.value = result.total || 0;
  } catch (e) {
    error.value = "Could not load records. Please check permissions and connection.";
  } finally {
    loading.value = false;
  }
}

watch(search, () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => load(false), 300);
});
watch(() => props.pageKey, () => { search.value = ""; load(false); });
onMounted(() => load(false));
</script>

<template>
  <section class="cmr-master-list-page">
    <PageHeader :title="title" :description="description">
      <template v-if="pageKey !== 'master-attributes'" #actions><button class="cmr-button primary" type="button" @click="emit('create')">+ New {{ title }}</button></template>
    </PageHeader>
    <div class="cmr-master-list-toolbar">
      <div class="cmr-master-search"><span>⌕</span><input v-model="search" :placeholder="`Search ${title.toLowerCase()}...`" /></div>
      <span class="cmr-record-count">{{ total }} records</span>
    </div>
    <div v-if="error" class="cmr-form-message error">{{ error }}</div>
    <section class="cmr-master-table-card">
      <table class="cmr-master-table">
        <thead><tr><th>#</th><th v-for="column in columns" :key="column.key">{{ column.label }}</th></tr></thead>
        <tbody>
          <tr v-for="(row, index) in records" :key="row.name" :class="{ 'cmr-editable-row': editable }" :title="editable ? 'Click to edit' : ''" @click="edit(row)">
            <td class="cmr-row-number">{{ index + 1 }}</td>
            <td v-for="column in columns" :key="column.key">
              <span v-if="column.status || column.enabledStatus" class="cmr-status-pill" :class="{ disabled: column.enabledStatus ? !row[column.key] : row.disabled }">{{ column.enabledStatus ? (row[column.key] ? 'Enabled' : 'Disabled') : (row.disabled ? 'Disabled' : 'Active') }}</span>
              <span v-else-if="column.numericStatus" class="cmr-status-pill">{{ row[column.key] ? 'Numeric' : 'Text' }}</span>
              <span v-else :class="{ 'cmr-primary-cell': column === columns[0] }">{{ row[column.key] || '—' }}</span>
            </td>
          </tr>
          <tr v-if="!loading && !records.length"><td :colspan="columns.length + 1" class="cmr-empty-records">No {{ title.toLowerCase() }} records found.</td></tr>
        </tbody>
      </table>
      <div v-if="loading" class="cmr-list-loading">Loading records…</div>
      <div v-if="!loading && records.length < total" class="cmr-load-more"><button class="cmr-button" type="button" @click="load(true)">Load More</button></div>
    </section>
  </section>
</template>

<style scoped>
.cmr-master-list-page{max-width:1180px;margin:0 auto 36px}.cmr-master-list-toolbar{margin-bottom:12px;padding:12px;display:flex;align-items:center;gap:12px;border:1px solid var(--dux-color-border-default,#e4e7ec);border-radius:12px;background:#fff}.cmr-master-search{position:relative;flex:1}.cmr-master-search span{position:absolute;left:13px;top:50%;transform:translateY(-50%);color:#8b94a7}.cmr-master-search input{width:100%;height:42px;padding:0 14px 0 36px;border:1px solid #d7dce5;border-radius:10px;outline:none;color:#151827;background:#fff}.cmr-master-search input:focus{border-color:#5c4de6;box-shadow:0 0 0 3px rgba(92,77,230,.12)}.cmr-record-count{white-space:nowrap;color:#667085;font-size:11px}.cmr-master-table-card{overflow:hidden;border:1px solid #e4e7ec;border-radius:14px;background:#fff;box-shadow:0 8px 24px rgba(16,24,40,.05)}.cmr-master-table{width:100%;border-collapse:collapse}.cmr-master-table th{padding:12px 16px;background:#f8f8fb;color:#7b8497;font-size:9px;font-weight:700;text-align:left;text-transform:uppercase;letter-spacing:.05em}.cmr-master-table td{padding:13px 16px;border-top:1px solid #eceef3;color:#475467;font-size:11px}.cmr-master-table tbody tr:hover{background:#faf9ff}.cmr-editable-row{cursor:pointer}.cmr-row-number{width:54px;color:#98a2b3!important}.cmr-primary-cell{color:#1d2233;font-weight:650}.cmr-status-pill{display:inline-flex;padding:4px 9px;border-radius:999px;background:#e7f8f4;color:#0e796d;font-size:9px;font-weight:700}.cmr-status-pill.disabled{background:#f2f4f7;color:#667085}.cmr-empty-records,.cmr-list-loading{text-align:center!important;padding:44px!important;color:#98a2b3!important}.cmr-list-loading,.cmr-load-more{padding:14px;text-align:center;border-top:1px solid #eceef3}.cmr-form-message{margin-bottom:12px}@media(max-width:700px){.cmr-master-list-toolbar{align-items:stretch;flex-direction:column}.cmr-master-table-card{overflow:auto}.cmr-master-table{min-width:680px}}
</style>
