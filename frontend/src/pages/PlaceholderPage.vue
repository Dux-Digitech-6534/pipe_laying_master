<script setup>
import { computed, ref, watch } from "vue";
import PageHeader from "../components/common/PageHeader.vue";
import CustomEntryForm from "./CustomEntryForm.vue";
import CustomMasterForm from "./CustomMasterForm.vue";
import MasterList from "./MasterList.vue";
import "../entry.css";

const props = defineProps({ title: String, description: String, pageKey: String, simpleMasters: Boolean });
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
  "master-material": { doctype: "Item", label: "Item", defaults: { is_stock_item: 1 } },
  "master-contractor": { doctype: "CMR Contractor Assignment", label: "Contractor Assignment" },
  "master-supplier": { doctype: "Supplier", label: "Supplier" },
  "master-store": { doctype: "Warehouse", label: "Store / Warehouse" },
  "master-attributes": { doctype: "Item Attribute", label: "Material Attribute" },
  "pipe-register": { doctype: "CMR Pipe Laying Measurement", label: "Pipe Laying Register", report: true },
  "material-movement": { doctype: "Stock Entry", label: "Material Movement", report: true },
  "material-stock": { doctype: "Stock Ledger Entry", label: "Material Stock", report: true },
  "contractor-stock": { doctype: "Stock Ledger Entry", label: "Contractor Stock", report: true },
  "valve-register": { doctype: "CMR Valve Installation", label: "Valve Register", report: true },
  "restoration-register": { doctype: "CMR Road Restoration", label: "Restoration Register", report: true },
};
const transactionKeys = ["material-inward", "material-issue", "material-return", "pipe-laying", "valves", "restoration"];
const masterKeys = ["master-project", "master-site", "master-material", "master-contractor", "master-supplier", "master-store", "master-attributes"];
const customListKeys = ["master-project", "master-site", "master-material"];
const config = computed(() => configs[props.pageKey]);
const canCreate = computed(() => config.value && !config.value.report);
const isTransaction = computed(() => transactionKeys.includes(props.pageKey));
const isMaster = computed(() => masterKeys.includes(props.pageKey));
const hasCustomList = computed(() => props.simpleMasters && customListKeys.includes(props.pageKey));
const creating = ref(false);
watch(() => props.pageKey, () => { creating.value = false; });

function newEntry() {
  if (!config.value) return;
  if (isTransaction.value || isMaster.value) { creating.value = true; return; }
  if (window.frappe) window.frappe.new_doc(config.value.doctype, config.value.defaults || {});
}
function openRecords() {
  if (config.value && window.frappe) window.frappe.set_route("List", config.value.doctype);
}
</script>

<template>
  <CustomEntryForm v-if="creating && isTransaction" :page-key="pageKey" :title="config.label" @close="creating = false" @create-master="emit('navigate', $event)" />
  <CustomMasterForm v-else-if="creating && isMaster" :page-key="pageKey" :title="config.label" :simple-masters="simpleMasters" @close="creating = false" @create-master="emit('navigate', $event)" />
  <MasterList v-else-if="hasCustomList" :page-key="pageKey" :title="title" :description="description" @create="newEntry" />
  <template v-else>
    <PageHeader :title="title" :description="description">
      <template #actions>
        <button class="cmr-button" type="button" @click="openRecords">Open Records</button>
        <button v-if="canCreate" class="cmr-button primary" type="button" @click="newEntry">+ New {{ config.label }}</button>
      </template>
    </PageHeader>
    <div class="cmr-entry-banner"><span>✓</span><div><b>{{ isTransaction || isMaster ? 'Modern CMR entry form ready' : 'Entry screen connected' }}</b><p>{{ isTransaction ? 'New entry portal ke andar open hogi aur backend me ERPNext document save karegi.' : `Records are connected to ${config?.doctype}.` }}</p></div></div>
    <section class="cmr-card cmr-entry-card">
      <div class="cmr-entry-icon">{{ pageKey.slice(0, 2).toUpperCase() }}</div><h3>{{ title }}</h3>
      <p>{{ canCreate ? 'Click New to create an entry in the CMR portal, or open existing records.' : 'Open the live backend register to view and filter records.' }}</p>
      <div class="cmr-entry-actions"><button class="cmr-button" type="button" @click="openRecords">Open Records</button><button v-if="canCreate" class="cmr-button primary" type="button" @click="newEntry">Create Entry</button></div>
    </section>
  </template>
</template>
