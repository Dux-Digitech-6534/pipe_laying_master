<script setup>
const props = defineProps({
  pageTitle: { type: String, required: true },
  user: { type: String, required: true },
  company: { type: String, required: true },
  financialYear: { type: String, required: true },
});
defineEmits(["toggle-sidebar"]);
function initials() { return props.user.split(" ").filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase(); }
function reloadPage() { window.location.reload(); }
</script>

<template>
  <header class="cmr-topbar">
    <div class="cmr-top-left"><button class="cmr-icon-button" type="button" aria-label="Toggle navigation" @click="$emit('toggle-sidebar')">☰</button><div class="cmr-breadcrumb"><span>Pipe Laying</span><i>/</i><b>{{ pageTitle }}</b></div></div>
    <div class="cmr-top-right">
      <div class="cmr-meta"><small>FINANCIAL YEAR</small><b>{{ financialYear }}</b></div>
      <button class="cmr-icon-button" type="button" title="Refresh" aria-label="Refresh" @click="reloadPage">↻</button>
      <button class="cmr-icon-button" type="button" title="Notifications" aria-label="Notifications">○</button>
      <span class="cmr-avatar">{{ initials() }}</span>
    </div>
  </header>
</template>
