<script setup>
import { computed, ref } from "vue";
import AppShell from "./components/layout/AppShell.vue";
import Dashboard from "./pages/Dashboard.vue";
import MasterSetup from "./pages/MasterSetup.vue";
import PlaceholderPage from "./pages/PlaceholderPage.vue";

const props = defineProps({ bootstrap: { type: Object, default: () => ({}) } });
const currentPage = ref("dashboard");

const pages = {
  dashboard: ["Dashboard", "Project execution and material overview"],
  "material-inward": ["Material Inward", "Manage received materials, suppliers and quantity breakup"],
  "material-issue": ["Material Issue", "Issue project material to stores or contractors"],
  "material-return": ["Material Return", "Record contractor material returns to project inventory"],
  "pipe-laying": ["Pipe Laying Measurement", "Capture measured pipeline execution and completion"],
  valves: ["Valve Details", "Record valve installation against registered pipe segments"],
  restoration: ["Road Restoration", "Track restoration work against pipe laying measurements"],
  masters: ["Masters & Settings", "Configure master data used by CMR workflows"],
  "master-project": ["Project Master", "Project setup for CMR execution sites"],
  "master-site": ["Site Master", "Project, zone, village and store mapping"],
  "master-material": ["Material Item", "Pipe, fitting, valve and consumable definitions"],
  "master-contractor": ["Contractor", "Execution contractor and site assignments"],
  "master-supplier": ["Supplier", "Material inward supplier master"],
  "master-store": ["Store", "Project and contractor stock locations"],
  "master-attributes": ["Material Attributes", "Reusable material specifications and UOM values"],
  "pipe-register": ["Pipe Laying Register", "Submitted pipe measurements"],
  "material-movement": ["Material Movement", "CMR stock movement register"],
  "material-stock": ["Material Stock", "Project and contractor stock visibility"],
  "contractor-stock": ["Contractor Stock", "Material currently held by contractors"],
  "valve-register": ["Valve Register", "Submitted valve installation register"],
  "restoration-register": ["Restoration Register", "Submitted road restoration register"],
};

const pageMeta = computed(() => pages[currentPage.value] || pages.dashboard);
const user = computed(() => props.bootstrap?.user || "Administrator");
const company = computed(() => props.bootstrap?.company || "Raisoni Group");
const financialYear = computed(() => props.bootstrap?.financial_year || "FY 26-27");
</script>

<template>
  <AppShell
    :active-page="currentPage"
    :page-title="pageMeta[0]"
    :user="user"
    :company="company"
    :financial-year="financialYear"
    @navigate="currentPage = $event"
  >
    <Dashboard v-if="currentPage === 'dashboard'" :user="user" :metrics="bootstrap.metrics" :recent-activity="bootstrap.recent_activity" @navigate="currentPage = $event" />
    <MasterSetup v-else-if="currentPage === 'masters'" @navigate="currentPage = $event" />
    <PlaceholderPage v-else :title="pageMeta[0]" :description="pageMeta[1]" :page-key="currentPage" @navigate="currentPage = $event" />
  </AppShell>
</template>
