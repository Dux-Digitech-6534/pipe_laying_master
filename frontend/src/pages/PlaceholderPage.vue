<script setup>
import { computed, ref, watch } from "vue";
import PageHeader from "../components/common/PageHeader.vue";
import CustomEntryForm from "./CustomEntryForm.vue";
import CustomMasterForm from "./CustomMasterForm.vue";
import PurchaseReturnForm from "./PurchaseReturnForm.vue";
import MasterList from "./MasterList.vue";
import ReportList from "./ReportList.vue";
import TransactionList from "./TransactionList.vue";
import "../entry.css";

const props = defineProps({ title: String, description: String, pageKey: String, simpleMasters: Boolean, enableMasterEdit: Boolean, hierarchyEnabled: Boolean, openRecordName: { type: String, default: "" } });
const emit = defineEmits(["navigate"]);
const configs = {
  "material-inward": { doctype: "Purchase Receipt", label: "Material Inward", defaults: { source_app: "CMR Pipe Laying Master" } },
  "material-issue": { doctype: "Stock Entry", label: "Material Issue" },
  "material-return": { doctype: "Stock Entry", label: "Material Return" },
  "pipe-laying": { doctype: "CMR Pipe Laying Measurement", label: "Pipe Laying Measurement" },
  valves: { doctype: "CMR Valve Installation", label: "Valve Installation" },
  restoration: { doctype: "CMR Road Restoration", label: "Road Restoration" },
  "master-project": { doctype: "Project", label: "Project" },
  "master-site": { doctype: "CMR Site", label: "Site" },
  "master-zone": { doctype: "CMR Zone", label: "Zone" },
  "master-village": { doctype: "CMR Village", label: "Village" },
  "master-material": { doctype: "Item", label: "Item", defaults: { is_stock_item: 1 } },
  "master-contractor": { doctype: "CMR Contractor Assignment", label: "Contractor Assignment" },
  "master-supplier": { doctype: "Supplier", label: "Supplier" },
  "master-store": { doctype: "Warehouse", label: "Store" },
  "master-attributes": { doctype: "Item Attribute", label: "Material Attribute" },
  "pipe-register": { doctype: "CMR Pipe Laying Measurement", label: "Pipe Laying Register", report: true },
  "material-movement": { doctype: "Stock Entry", label: "Material Movement", report: true },
  "material-stock": { doctype: "Stock Ledger Entry", label: "Material Stock", report: true },
  "contractor-stock": { doctype: "Stock Ledger Entry", label: "Contractor Stock", report: true },
  "valve-register": { doctype: "CMR Valve Installation", label: "Valve Register", report: true },
  "restoration-register": { doctype: "CMR Road Restoration", label: "Restoration Register", report: true },
};
const transactionKeys = ["material-inward", "material-issue", "material-return", "pipe-laying", "valves", "restoration"];
const masterKeys = ["master-project", "master-site", "master-zone", "master-village", "master-material", "master-contractor", "master-supplier", "master-store", "master-attributes"];
const customListKeys = ["master-project", "master-site", "master-zone", "master-village", "master-material", "master-contractor", "master-supplier", "master-store", "master-attributes"];
const config = computed(() => configs[props.pageKey]);
const canCreate = computed(() => config.value && !config.value.report);
const isTransaction = computed(() => transactionKeys.includes(props.pageKey));
const isMaster = computed(() => masterKeys.includes(props.pageKey));
const hasCustomList = computed(() => props.simpleMasters && customListKeys.includes(props.pageKey));
const isReport = computed(() => Boolean(config.value?.report));
const creating = ref(false);
const listRefresh = ref(0);
const editingRecord = ref("");
const returnAgainst = ref("");
const returnRecord = ref("");
watch(() => props.pageKey, () => {
  creating.value = false; editingRecord.value = ""; returnAgainst.value = ""; returnRecord.value = "";
  if (props.openRecordName && props.enableMasterEdit && isTransaction.value) {
    editingRecord.value = props.openRecordName;
    creating.value = true;
  }
}, { immediate: true });

function newEntry() {
  if (!config.value) return;
  editingRecord.value = "";
  if (isTransaction.value || isMaster.value) { creating.value = true; return; }
  if (window.frappe) window.frappe.new_doc(config.value.doctype, config.value.defaults || {});
}
function editEntry(recordName) {
  if (!props.enableMasterEdit) return;
  editingRecord.value = recordName;
  creating.value = true;
}
function startPurchaseReturn(sourceName) { returnAgainst.value = sourceName; returnRecord.value = ""; creating.value = false; }
function editPurchaseReturn(recordName) { returnRecord.value = recordName; returnAgainst.value = ""; creating.value = false; }
function closePurchaseReturn() { returnAgainst.value = ""; returnRecord.value = ""; listRefresh.value += 1; }
function showBackendList() {
  creating.value = false;
  listRefresh.value += 1;
}
function handleMasterSaved() {
  creating.value = false;
  listRefresh.value += 1;
}
</script>

<template>
  <PurchaseReturnForm v-if="returnAgainst || returnRecord" :source-name="returnAgainst" :record-name="returnRecord" @close="closePurchaseReturn" />
  <CustomEntryForm v-else-if="creating && isTransaction" :page-key="pageKey" :title="config.label" :record-name="editingRecord" :hierarchy-enabled="hierarchyEnabled" @close="creating = false" @saved="showBackendList" @return-material="startPurchaseReturn" @edit-return="editPurchaseReturn" @create-master="emit('navigate', $event)" />
  <CustomMasterForm v-else-if="creating && isMaster" :page-key="pageKey" :title="config.label" :simple-masters="simpleMasters" :record-name="editingRecord" :hierarchy-enabled="hierarchyEnabled" @close="creating = false" @saved="handleMasterSaved" @create-master="emit('navigate', $event)" />
  <TransactionList v-else-if="simpleMasters && isTransaction" :key="`${pageKey}-${listRefresh}`" :page-key="pageKey" :title="title" :description="description" :editable="enableMasterEdit" @create="newEntry" @edit="editEntry" />
  <MasterList v-else-if="hasCustomList" :page-key="pageKey" :title="title" :description="description" :editable="enableMasterEdit" @create="newEntry" @edit="editEntry" />
  <ReportList v-else-if="isReport" :page-key="pageKey" :title="title" :description="description" />
  <template v-else>
    <PageHeader :title="title" :description="description">
      <template #actions>
        <button v-if="canCreate" class="cmr-button primary" type="button" @click="newEntry">+ New {{ config.label }}</button>
      </template>
    </PageHeader>
    <div class="cmr-entry-banner"><span>✓</span><div><b>{{ isTransaction || isMaster ? 'Modern entry form ready' : 'Entry screen connected' }}</b><p>{{ isTransaction ? 'The new entry opens inside the portal and saves as an ERPNext document in the backend.' : `Records are connected to ${config?.doctype}.` }}</p></div></div>
    <section class="cmr-card cmr-entry-card">
      <div class="cmr-entry-icon">{{ pageKey.slice(0, 2).toUpperCase() }}</div><h3>{{ title }}</h3>
      <p>{{ canCreate ? 'Click New to create an entry in the Pipe Laying portal, or open existing records.' : 'Open the live backend register to view and filter records.' }}</p>
      <div class="cmr-entry-actions"><button v-if="canCreate" class="cmr-button primary" type="button" @click="newEntry">Create Entry</button></div>
    </section>
  </template>
</template>
