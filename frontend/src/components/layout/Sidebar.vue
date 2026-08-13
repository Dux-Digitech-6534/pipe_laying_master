<script setup>
import { computed, ref } from "vue";
import NavIcon from "./NavIcon.vue";

const props = defineProps({ activePage: { type: String, required: true }, collapsed: { type: Boolean, default: false }, user: { type: String, required: true }, simpleMasters: { type: Boolean, default: false } });
defineEmits(["navigate"]);
const search = ref("");
const groups = computed(() => [
  { label: "", items: [["dashboard", "Dashboard", "dashboard"]] },
  { label: "Material Management", items: [["material-inward", "Material Inward", "inward"], ["material-issue", "Material Issue", "issue"], ["material-return", "Material Return", "return"]] },
  { label: "Pipe Execution", items: [["pipe-laying", "Pipe Laying Measurement", "pipe"], ["valves", "Valve Details", "valve"], ["restoration", "Road Restoration", "restoration"]] },
  ...(props.simpleMasters ? [{ label: "Masters & Settings", items: [["master-project", "Project", "project"], ["master-site", "Site", "site"], ["master-material", "Item", "item"], ["master-contractor", "Contractor", "contractor"], ["master-supplier", "Supplier", "supplier"], ["master-store", "Store", "store"], ["master-attributes", "Material Attributes", "attribute"]] }] : [{ label: "Masters & Settings", items: [["masters", "Master Setup", "setup"], ["master-project", "Project Master", "project"], ["master-site", "Site Master", "site"], ["master-material", "Material Item", "item"], ["master-contractor", "Contractor", "contractor"], ["master-supplier", "Supplier", "supplier"], ["master-store", "Store", "store"], ["master-attributes", "Material Attributes", "attribute"]] }]),
  { label: "Reports", items: [["pipe-register", "Pipe Laying Register", "report"], ["material-movement", "Material Movement", "movement"], ["material-stock", "Material Stock", "stock"], ["contractor-stock", "Contractor Stock", "item"], ["valve-register", "Valve Register", "valve"], ["restoration-register", "Restoration Register", "restoration"]] },
]);
const visibleGroups = computed(() => { const query = search.value.trim().toLowerCase(); if (!query) return groups.value; return groups.value.map(group => ({ ...group, items: group.items.filter(item => item[1].toLowerCase().includes(query)) })).filter(group => group.items.length); });
const initials = computed(() => props.user.split(" ").filter(Boolean).slice(0, 2).map(part => part[0]).join("").toUpperCase());
</script>

<template>
  <aside class="cmr-sidebar" :class="{ collapsed }">
    <div class="cmr-brand"><span class="cmr-brand-mark">CMR</span><span class="cmr-brand-copy"><b>CMR PIPE LAYING</b><small>Execution Master</small></span></div>
    <div class="cmr-search-wrap"><div class="cmr-search-box"><span>⌕</span><input v-model="search" aria-label="Search menu" placeholder="Search menu..." /></div></div>
    <nav class="cmr-navigation" aria-label="CMR application navigation">
      <section v-for="group in visibleGroups" :key="group.label" class="cmr-nav-group">
        <div v-if="group.label" class="cmr-nav-label">{{ group.label }}</div>
        <button v-for="item in group.items" :key="item[0]" type="button" class="cmr-nav-item" :class="{ active: activePage === item[0] }" :title="item[1]" @click="$emit('navigate', item[0])"><span class="cmr-nav-icon"><NavIcon :name="item[2]" /></span><span class="cmr-nav-text">{{ item[1] }}</span></button>
      </section>
    </nav>
    <div class="cmr-sidebar-footer"><span class="cmr-avatar">{{ initials }}</span><span class="cmr-profile-copy"><b>{{ user }}</b><small>Project Operations</small></span></div>
  </aside>
</template>
