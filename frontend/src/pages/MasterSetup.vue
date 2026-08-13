<script setup>
import PageHeader from "../components/common/PageHeader.vue";
defineEmits(["navigate"]);
const masters = [
  ["master-project", "Project Master", "Create projects used by CMR sites and execution records.", "P"],
  ["master-site", "Site Master", "Create project, zone, village, site incharge and store mapping.", "⌂"],
  ["master-material", "Material Item", "Define pipes, fittings, valves and consumable inventory items.", "□"],
  ["master-contractor", "Contractor", "Maintain execution contractors and explicit site assignments.", "♙"],
  ["master-supplier", "Supplier", "Maintain suppliers used for project material inward.", "⇥"],
  ["master-store", "Store", "Map project and contractor warehouses used for stock movement.", "▤"],
  ["master-attributes", "Material Attributes", "Configure item type, MOC, class, size and UOM values.", "≡"],
];
</script>

<template>
  <PageHeader title="Masters & Settings" description="Configure the master data that feeds transaction screens across the CMR Pipe Laying application." />
  <div class="cmr-settings-band"><div class="cmr-settings-copy"><span class="cmr-band-icon">☷</span><div><b>Central master data setup</b><p>Use these masters before starting transactions. Standard ERPNext Item, Supplier and Warehouse records remain the source of truth.</p></div></div><span class="cmr-badge info">Configuration</span></div>
  <div class="cmr-master-grid">
    <article v-for="master in masters" :key="master[0]" class="cmr-master-card">
      <div class="cmr-master-top"><span>{{ master[3] }}</span><small>MASTER</small></div>
      <h3>{{ master[1] }}</h3><p>{{ master[2] }}</p>
      <div class="cmr-master-foot"><span><b>—</b> records</span><button type="button" @click="$emit('navigate', master[0])">Open ›</button></div>
    </article>
  </div>
  <section class="cmr-card">
    <div class="cmr-card-head"><b>Recommended setup sequence</b><span>Required before transactions</span></div>
    <div class="cmr-timeline cmr-sequence">
      <div><i></i><span><b>1. Material Attributes</b><small>Create item type, MOC, class, size and UOM values.</small></span></div>
      <div><i></i><span><b>2. Material Items</b><small>Build pipe, fitting, valve and consumable items.</small></span></div>
      <div><i></i><span><b>3. Sites & Stores</b><small>Create the execution hierarchy and stock locations.</small></span></div>
      <div><i></i><span><b>4. Contractors & Suppliers</b><small>Complete parties and assignments before transactions.</small></span></div>
    </div>
  </section>
</template>
