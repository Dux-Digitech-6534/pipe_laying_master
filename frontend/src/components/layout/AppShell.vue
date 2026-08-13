<script setup>
import { ref } from "vue";
import Sidebar from "./Sidebar.vue";
import TopHeader from "./TopHeader.vue";

defineProps({ activePage: String, pageTitle: String, user: String, company: String, financialYear: String });
defineEmits(["navigate"]);
const sidebarOpen = ref(false);
const collapsed = ref(false);
function toggleSidebar() {
  if (window.innerWidth <= 780) sidebarOpen.value = !sidebarOpen.value;
  else collapsed.value = !collapsed.value;
}
</script>

<template>
  <div class="cmr-app" :class="{ 'sidebar-open': sidebarOpen, collapsed }">
    <Sidebar :active-page="activePage" :collapsed="collapsed" :user="user" @navigate="(page) => { $emit('navigate', page); sidebarOpen = false; }" />
    <div class="cmr-main">
      <TopHeader :page-title="pageTitle" :user="user" :company="company" :financial-year="financialYear" @toggle-sidebar="toggleSidebar" />
      <main class="cmr-content"><slot /></main>
    </div>
    <button v-if="sidebarOpen" class="cmr-sidebar-scrim" aria-label="Close navigation" @click="sidebarOpen = false" />
  </div>
</template>
