<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";
import Sidebar from "./Sidebar.vue";
import TopHeader from "./TopHeader.vue";

defineProps({ activePage: String, pageTitle: String, user: String, company: String, financialYear: String, simpleMasters: Boolean, hierarchyMasters: Boolean });
defineEmits(["navigate"]);
const sidebarOpen = ref(false);
const collapsed = ref(window.innerWidth <= 1200);
let collapseTouched = false;
function toggleSidebar() {
  if (window.innerWidth <= 820) sidebarOpen.value = !sidebarOpen.value;
  else { collapsed.value = !collapsed.value; collapseTouched = true; }
}
function syncCollapsedForWidth() {
  if (window.innerWidth > 820 && !collapseTouched) collapsed.value = window.innerWidth <= 1200;
}
onMounted(() => window.addEventListener("resize", syncCollapsedForWidth));
onBeforeUnmount(() => window.removeEventListener("resize", syncCollapsedForWidth));
</script>

<template>
  <div class="cmr-app" :class="{ 'sidebar-open': sidebarOpen, collapsed }">
    <Sidebar :active-page="activePage" :collapsed="collapsed" :user="user" :simple-masters="simpleMasters" :hierarchy-masters="hierarchyMasters" @navigate="(page) => { $emit('navigate', page); sidebarOpen = false; }" />
    <div class="cmr-main">
      <TopHeader :page-title="pageTitle" :user="user" :company="company" :financial-year="financialYear" @toggle-sidebar="toggleSidebar" />
      <main class="cmr-content"><slot /></main>
    </div>
    <button v-if="sidebarOpen" class="cmr-sidebar-scrim" aria-label="Close navigation" @click="sidebarOpen = false" />
  </div>
</template>
