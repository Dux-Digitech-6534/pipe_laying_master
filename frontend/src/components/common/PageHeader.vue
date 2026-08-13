<script setup>
defineProps({
  eyebrow: { type: String, default: "CMR PORTAL / PIPE LAYING" },
  title: { type: String, required: true },
  description: { type: String, required: true },
});
</script>

<template>
  <div class="cmr-page-header">
    <div>
      <div class="cmr-eyebrow">{{ eyebrow }}</div>
      <h1>{{ title }}</h1>
      <p>{{ description }}</p>
    </div>
    <div v-if="$slots.actions" class="cmr-page-actions"><slot name="actions" /></div>
  </div>
</template>
