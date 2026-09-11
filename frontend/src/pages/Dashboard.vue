<script setup>
import PageHeader from "../components/common/PageHeader.vue";
const props = defineProps({
  user: { type: String, required: true },
  metrics: { type: Object, default: () => ({}) },
  recentActivity: { type: Array, default: () => [] },
});
const emit = defineEmits(["navigate"]);
const metricCards = [
  ["Pending Approvals", "pending_approvals", "▤", "purple"],
  ["Material Inward This Month", "material_inward_this_month", "↓", "green"],
  ["Pipe Laying Completed", "pipe_laying_completed", "⌁", "amber"],
  ["Pending Restoration", "pending_restoration", "≋", "blue"],
];
const ACTIVITY_PAGE_MAP = {
  "CMR Pipe Laying Measurement": "pipe-laying",
  "CMR Valve Installation": "valves",
  "CMR Road Restoration": "restoration",
};
function openActivity(row) {
  const pageKey = ACTIVITY_PAGE_MAP[row.doctype];
  if (pageKey) emit("navigate", pageKey, row.reference);
}
</script>

<template>
  <PageHeader :title="`Good morning, ${user}`" description="Here is your CMR pipe laying activity summary." />
  <div class="cmr-stat-grid">
    <article v-for="metric in metricCards" :key="metric[0]" class="cmr-stat-card">
      <div class="cmr-stat-top"><span class="cmr-stat-icon" :class="metric[3]">{{ metric[2] }}</span><span class="cmr-live-label">LIVE DATA</span></div>
      <strong>{{ props.metrics?.[metric[1]] ?? 0 }}</strong><small>{{ metric[0] }}</small>
    </article>
  </div>
  <div class="cmr-two-column">
    <section class="cmr-card">
      <div class="cmr-card-head"><b>Recent Activity</b><span>Latest documents</span></div>
      <div class="cmr-table-wrap"><table class="cmr-table"><thead><tr><th>Document</th><th>Reference</th><th>Project</th><th>Date</th><th>Status</th></tr></thead><tbody>
        <tr v-for="row in recentActivity" :key="`${row.doctype}-${row.reference}`" class="cmr-clickable-row" @click="openActivity(row)"><td>{{ row.document }}</td><td>{{ row.reference }}</td><td>{{ row.project || '—' }}</td><td>{{ row.date || '—' }}</td><td><span class="cmr-badge info">{{ row.status || 'Draft' }}</span></td></tr>
        <tr v-if="!recentActivity.length"><td colspan="5"><div class="cmr-table-empty"><span>▤</span><b>No CMR transactions yet</b><small>New CMR records will appear here automatically.</small></div></td></tr>
      </tbody></table></div>
    </section>
    <section class="cmr-card">
      <div class="cmr-card-head"><b>Getting Started</b><span>Recommended order</span></div>
      <div class="cmr-timeline">
        <button type="button" @click="$emit('navigate', 'masters')"><i></i><span><b>Configure masters</b><small>Sites, items, contractors, suppliers and stores</small></span></button>
        <button type="button" @click="$emit('navigate', 'material-inward')"><i></i><span><b>Receive project material</b><small>Create material inward after master setup</small></span></button>
        <button type="button" @click="$emit('navigate', 'pipe-laying')"><i></i><span><b>Record pipe execution</b><small>Capture measured work against available stock</small></span></button>
      </div>
      <div class="cmr-progress-block"><div><span>Power App migration</span><b>Core workflows ready</b></div><div class="cmr-progress"><i style="width: 100%"></i></div></div>
    </section>
  </div>
</template>