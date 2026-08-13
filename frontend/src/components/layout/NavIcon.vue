<script setup>
const props = defineProps({ name: { type: String, default: "circle" } });
const paths = {
  dashboard: ["M4 4h6v6H4z", "M14 4h6v6h-6z", "M4 14h6v6H4z", "M14 14h6v6h-6z"],
  inward: ["M12 3v12", "m7 10 5 5 5-5", "M5 20h14"],
  issue: ["M12 21V9", "m17 14-5-5-5 5", "M5 4h14"],
  return: ["M3 12a9 9 0 1 0 3-6.7", "M3 4v5h5"],
  pipe: ["M3 8h5v8H3z", "M16 8h5v8h-5z", "M8 12h8"],
  valve: ["M4 8l8 4-8 4z", "M20 8l-8 4 8 4z", "M12 4v16"],
  restoration: ["M4 6h16", "M4 12h16", "M4 18h16", "m8 3-2 6", "m16 9-2 6"],
  setup: ["M4 6h16", "M4 12h16", "M4 18h16", "M8 4v4", "M16 10v4", "M10 16v4"],
  project: ["M3 7h7l2 2h9v10H3z", "M3 7V5h7l2 2"],
  site: ["M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0z", "M12 10a2 2 0 1 0 0-4 2 2 0 0 0 0 4z"],
  item: ["m12 3 8 4-8 4-8-4z", "m4 7 8 4 8-4", "v10l-8 4-8-4V7", "M12 11v10"],
  contractor: ["M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z", "M3 21v-2a6 6 0 0 1 12 0v2", "M16 11h5", "m19 8 3 3-3 3"],
  supplier: ["M3 7h11v10H3z", "M14 10h4l3 3v4h-7z", "M7 20a2 2 0 1 0 0-4 2 2 0 0 0 0 4z", "M18 20a2 2 0 1 0 0-4 2 2 0 0 0 0 4z"],
  store: ["M4 8h16v12H4z", "M3 4h18l-1 4H4z", "M9 12h6"],
  attribute: ["M4 7h10", "M18 7h2", "M4 17h2", "M10 17h10", "M14 4v6", "M6 14v6"],
  report: ["M5 3h10l4 4v14H5z", "M15 3v5h5", "M8 13h8", "M8 17h6"],
  movement: ["M4 8h13", "m14 5 3 3-3 3", "M20 16H7", "m10 13-3 3 3 3"],
  stock: ["M4 19V9", "M10 19V5", "M16 19v-7", "M22 19V3"],
};
</script>

<template>
  <svg viewBox="0 0 24 24" aria-hidden="true"><path v-for="path in (paths[props.name] || paths.report)" :key="path" :d="path" /></svg>
</template>

<style scoped>svg{width:16px;height:16px;fill:none;stroke:currentColor;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}</style>
