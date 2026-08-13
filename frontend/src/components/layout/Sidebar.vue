<script setup>
import { computed, ref } from "vue";

const props = defineProps({
  activePage: { type: String, required: true },
  collapsed: { type: Boolean, default: false },
  user: { type: String, required: true },
});
defineEmits(["navigate"]);
const search = ref("");

const groups = [
  { label: "", items: [["dashboard", "Dashboard", "▦"]] },
  { label: "Material Management", items: [["material-inward", "Material Inward", "↓"], ["material-issue", "Material Issue", "↑"], ["material-return", "Material Return", "↻"]] },
  { label: "Pipe Execution", items: [["pipe-laying", "Pipe Laying Measurement", "⌁"], ["valves", "Valve Details", "⚙"], ["restoration", "Road Restoration", "≋"]] },
  { label: "Masters & Settings", items: [["masters", "Master Setup", "☷"], ["master-project", "Project Master", "P"], ["master-site", "Site Master", "⌂"], ["master-material", "Material Item", "□"], ["master-contractor", "Contractor", "♙"], ["master-supplier", "Supplier", "⇥"], ["master-store", "Store", "▤"], ["master-attributes", "Material Attributes", "≡"]] },
  { label: "Reports", items: [["pipe-register", "Pipe Laying Register", "▥"], ["material-movement", "Material Movement", "☰"], ["material-stock", "Material Stock", "▣"], ["contractor-stock", "Contractor Stock", "▧"], ["valve-register", "Valve Register", "◉"], ["restoration-register", "Restoration Register", "▱"]] },
];

const visibleGroups = computed(() => {
  const query = search.value.trim().toLowerCase();
  if (!query) return groups;
  return groups.map((group) => ({ ...group, items: group.items.filter((item) => item[1].toLowerCase().includes(query)) })).filter((group) => group.items.length);
});
const initials = computed(() => props.user.split(" ").filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase());
</script>

<template>
  <aside class="cmr-sidebar" :class="{ collapsed }">
    <div class="cmr-brand">
      <span class="cmr-brand-mark">CMR</span>
      <span class="cmr-brand-copy"><b>CMR PIPE LAYING</b><small>Execution Master</small></span>
    </div>
    <div class="cmr-search-wrap">
      <div class="cmr-search-box"><span>⌕</span><input v-model="search" aria-label="Search menu" placeholder="Search menu..." /></div>
    </div>
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
