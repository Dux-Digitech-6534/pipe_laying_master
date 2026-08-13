<script setup>
import { computed, ref } from "vue";

const props = defineProps({
  activePage: { type: String, required: true },
  collapsed: { type: Boolean, default: false },
  user: { type: String, required: true },
  simpleMasters: { type: Boolean, default: false },
});
defineEmits(["navigate"]);
const search = ref("");

const groups = computed(() => [
  { label: "", items: [["dashboard", "Dashboard", "D"]] },
  { label: "Material Management", items: [["material-inward", "Material Inward", "IN"], ["material-issue", "Material Issue", "IS"], ["material-return", "Material Return", "RT"]] },
  { label: "Pipe Execution", items: [["pipe-laying", "Pipe Laying Measurement", "PL"], ["valves", "Valve Details", "V"], ["restoration", "Road Restoration", "RR"]] },
  ...(props.simpleMasters ? [
    { label: "Masters & Settings", items: [["master-project", "Project", "P"], ["master-site", "Site", "S"], ["master-material", "Item", "I"], ["master-contractor", "Contractor", "C"], ["master-supplier", "Supplier", "SP"], ["master-store", "Store", "ST"], ["master-attributes", "Material Attributes", "A"]] },
  ] : [
    { label: "Masters & Settings", items: [["masters", "Master Setup", "M"], ["master-project", "Project Master", "P"], ["master-site", "Site Master", "S"], ["master-material", "Material Item", "I"], ["master-contractor", "Contractor", "C"], ["master-supplier", "Supplier", "SP"], ["master-store", "Store", "ST"], ["master-attributes", "Material Attributes", "A"]] },
  ]),
  { label: "Reports", items: [["pipe-register", "Pipe Laying Register", "PR"], ["material-movement", "Material Movement", "MM"], ["material-stock", "Material Stock", "MS"], ["contractor-stock", "Contractor Stock", "CS"], ["valve-register", "Valve Register", "VR"], ["restoration-register", "Restoration Register", "RR"]] },
]);

const visibleGroups = computed(() => {
  const query = search.value.trim().toLowerCase();
  if (!query) return groups.value;
  return groups.value.map((group) => ({ ...group, items: group.items.filter((item) => item[1].toLowerCase().includes(query)) })).filter((group) => group.items.length);
});
const initials = computed(() => props.user.split(" ").filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase());
</script>

<template>
  <aside class="cmr-sidebar" :class="{ collapsed }">
    <div class="cmr-brand">
      <span class="cmr-brand-mark">CMR</span>
      <span class="cmr-brand-copy"><b>CMR PIPE LAYING</b><small>Execution Master</small></span>
    </div>
    <div class="cmr-search-wrap"><div class="cmr-search-box"><span>⌕</span><input v-model="search" aria-label="Search menu" placeholder="Search menu..." /></div></div>
    <nav class="cmr-navigation" aria-label="CMR application navigation">
      <section v-for="group in visibleGroups" :key="group.label" class="cmr-nav-group">
        <div v-if="group.label" class="cmr-nav-label">{{ group.label }}</div>
        <button v-for="item in group.items" :key="item[0]" type="button" class="cmr-nav-item" :class="{ active: activePage === item[0] }" :title="item[1]" @click="$emit('navigate', item[0])">
          <span class="cmr-nav-icon">{{ item[2] }}</span><span class="cmr-nav-text">{{ item[1] }}</span>
        </button>
      </section>
    </nav>
    <div class="cmr-sidebar-footer"><span class="cmr-avatar">{{ initials }}</span><span class="cmr-profile-copy"><b>{{ user }}</b><small>Project Operations</small></span></div>
  </aside>
</template>
