<script setup>
import { computed, onMounted, ref, watch } from "vue";
import PageHeader from "../components/common/PageHeader.vue";

const props = defineProps({ pageKey: String, title: String, description: String, editable: Boolean });
const emit = defineEmits(["create", "edit"]);
const records = ref([]);
const total = ref(0);
const search = ref("");
const status = ref("");
const loading = ref(false);
const error = ref("");
let timer;

const columns = computed(() => ({
  "material-inward": [
    { key: "name", label: "Document" },
    { key: "supplier", label: "Supplier" },
    { key: "custom_cmr_site", label: "Site" },
    { key: "posting_date", label: "Date" },
    { key: "grand_total", label: "Total", number: true },
  ],
  "material-issue": [{ key: "name", label: "Document" }, { key: "custom_cmr_site", label: "Site" }, { key: "posting_date", label: "Date" }],
  "material-return": [{ key: "name", label: "Document" }, { key: "custom_cmr_site", label: "Site" }, { key: "posting_date", label: "Date" }],
  "pipe-laying": [{ key: "name", label: "Document" }, { key: "project", label: "Project" }, { key: "site", label: "Site" }, { key: "laying_date", label: "Date" }],
  valves: [{ key: "name", label: "Document" }, { key: "project", label: "Project" }, { key: "site", label: "Site" }, { key: "installation_date", label: "Date" }],
  restoration: [{ key: "name", label: "Document" }, { key: "project", label: "Project" }, { key: "site", label: "Site" }, { key: "restoration_date", label: "Date" }],
}[props.pageKey] || []));

function call(method, args = {}) { return new Promise((resolve, reject) => window.frappe.call({ method, args, callback: r => resolve(r.message), error: reject })); }
function label(row) { return row.docstatus === 0 ? "Draft" : row.docstatus === 1 ? "Submitted" : "Cancelled"; }
async function load(append = false) {
  loading.value = true; error.value = "";
  try {
    const result = await call("cmr_pipe_laying_master.api.entries.get_entry_records", { entry_type: props.pageKey, search: search.value, status: status.value, start: append ? records.value.length : 0, page_length: 50 });
    records.value = append ? [...records.value, ...(result.records || [])] : (result.records || []);
    total.value = result.total || 0;
  } catch (e) { error.value = "Could not load records. Please check permissions and connection."; }
  finally { loading.value = false; }
}
function open(row) {
  if (props.editable) {
    emit("edit", row.name);
    return;
  }
  if (window.frappe) window.frappe.set_route("Form", row.doctype, row.name);
}
watch([search, status], () => { clearTimeout(timer); timer = setTimeout(() => load(false), 250); });
onMounted(() => load(false));
</script>

<template>
  <section class="cmr-master-list-page">
    <PageHeader :title="title" :description="description"><template #actions><button class="cmr-button primary" type="button" @click="emit('create')">+ New {{ title }}</button></template></PageHeader>
    <div class="cmr-master-list-toolbar">
      <div class="cmr-master-search"><span>⌕</span><input v-model="search" :placeholder="`Search ${title.toLowerCase()}...`" /></div>
      <select v-model="status" class="cmr-status-filter"><option value="">All Status</option><option value="0">Draft</option><option value="1">Submitted</option><option value="2">Cancelled</option></select>
      <span class="cmr-record-count">{{ total }} records</span>
    </div>
    <div v-if="error" class="cmr-form-message error">{{ error }}</div>
    <section class="cmr-master-table-card">
      <table class="cmr-master-table">
        <thead><tr><th>#</th><th v-for="column in columns" :key="column.key">{{ column.label }}</th><th>Status</th></tr></thead>
        <tbody>
          <tr v-for="(row,index) in records" :key="row.name" class="cmr-clickable-row" :title="editable ? 'Open in Pipe Laying portal' : 'Open ERPNext document'" @click="open(row)">
            <td class="cmr-row-number">{{ index + 1 }}</td>
            <td v-for="(column,columnIndex) in columns" :key="column.key"><span :class="{ 'cmr-primary-cell': columnIndex === 0 }">{{ column.number ? Number(row[column.key] || 0).toFixed(2) : (row[column.key] || '—') }}</span></td>
            <td><span class="cmr-status-pill" :class="`status-${row.docstatus}`">{{ label(row) }}</span></td>
          </tr>
          <tr v-if="!loading && !records.length"><td :colspan="columns.length + 2" class="cmr-empty-records">No records found.</td></tr>
        </tbody>
      </table>
      <div v-if="loading" class="cmr-list-loading">Loading records…</div>
      <div v-if="!loading && records.length < total" class="cmr-load-more"><button class="cmr-button" type="button" @click="load(true)">Load More</button></div>
    </section>
  </section>
</template>

<style scoped>
.cmr-master-list-page{max-width:1180px;margin:0 auto 36px}.cmr-master-list-toolbar{margin-bottom:12px;padding:12px;display:flex;align-items:center;gap:12px;border:1px solid #e4e7ec;border-radius:12px;background:#fff}.cmr-master-search{position:relative;flex:1}.cmr-master-search span{position:absolute;left:13px;top:50%;transform:translateY(-50%);color:#8b94a7}.cmr-master-search input,.cmr-status-filter{height:42px;border:1px solid #d7dce5;border-radius:10px;outline:none;background:#fff;color:#151827}.cmr-master-search input{width:100%;padding:0 14px 0 36px}.cmr-status-filter{min-width:145px;padding:0 12px}.cmr-master-search input:focus,.cmr-status-filter:focus{border-color:#5c4de6;box-shadow:0 0 0 3px rgba(92,77,230,.12)}.cmr-record-count{white-space:nowrap;color:#667085;font-size:11px}.cmr-master-table-card{overflow:hidden;border:1px solid #e4e7ec;border-radius:14px;background:#fff;box-shadow:0 8px 24px rgba(16,24,40,.05)}.cmr-master-table{width:100%;border-collapse:collapse}.cmr-master-table th{padding:12px 16px;background:#f8f8fb;color:#7b8497;font-size:9px;text-align:left;text-transform:uppercase;letter-spacing:.05em}.cmr-master-table td{padding:13px 16px;border-top:1px solid #eceef3;color:#475467;font-size:11px}.cmr-clickable-row{cursor:pointer}.cmr-clickable-row:hover{background:#faf9ff}.cmr-row-number{width:54px;color:#98a2b3!important}.cmr-primary-cell{color:#3730a3;font-weight:700}.cmr-status-pill{display:inline-flex;padding:4px 9px;border-radius:999px;font-size:9px;font-weight:700}.status-0{background:#fff4e5;color:#a15c00}.status-1{background:#e7f8f4;color:#0e796d}.status-2{background:#fdecef;color:#b4233d}.cmr-empty-records,.cmr-list-loading{text-align:center!important;padding:44px!important;color:#98a2b3!important}.cmr-list-loading,.cmr-load-more{padding:14px;text-align:center;border-top:1px solid #eceef3}@media(max-width:700px){.cmr-master-list-toolbar{align-items:stretch;flex-direction:column}.cmr-master-table-card{overflow:auto}.cmr-master-table{min-width:760px}}
</style>
