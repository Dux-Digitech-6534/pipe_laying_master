<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps({
  modelValue: { type: [String, Number], default: "" },
  options: { type: Array, default: () => [] },
  valueKey: { type: String, default: "name" },
  labelKey: { type: String, default: "name" },
  secondaryKey: { type: String, default: "" },
  placeholder: { type: String, default: "Search and select…" },
  createLabel: { type: String, default: "" },
  disabled: { type: Boolean, default: false },
});
const emit = defineEmits(["update:modelValue", "change", "create"]);
const root = ref(null);
const searchInput = ref(null);
const open = ref(false);
const query = ref("");
const activeIndex = ref(0);

const normalized = computed(() => props.options.map(option => typeof option === "object" ? option : ({ name: option })));
const selected = computed(() => normalized.value.find(option => String(option[props.valueKey] ?? "") === String(props.modelValue ?? "")));
const filtered = computed(() => {
  const term = query.value.trim().toLowerCase();
  if (!term) return normalized.value.slice(0, 80);
  return normalized.value.filter(option => {
    const primary = String(option[props.labelKey] ?? "").toLowerCase();
    const value = String(option[props.valueKey] ?? "").toLowerCase();
    const secondary = props.secondaryKey ? String(option[props.secondaryKey] ?? "").toLowerCase() : "";
    return primary.includes(term) || value.includes(term) || secondary.includes(term);
  }).slice(0, 80);
});
const displayValue = computed(() => open.value ? query.value : String(selected.value?.[props.labelKey] ?? ""));

watch(() => props.modelValue, () => { if (!open.value) query.value = ""; });
watch(filtered, () => { activeIndex.value = 0; });

async function show() {
  if (props.disabled) return;
  open.value = true;
  query.value = "";
  activeIndex.value = 0;
  await nextTick();
  searchInput.value?.focus();
}
function choose(option) {
  const value = option[props.valueKey];
  emit("update:modelValue", value);
  emit("change", option);
  open.value = false;
  query.value = "";
}
function clear() {
  emit("update:modelValue", "");
  emit("change", null);
  query.value = "";
  show();
}
function keydown(event) {
  if (!open.value && ["Enter", "ArrowDown", " "].includes(event.key)) { event.preventDefault(); show(); return; }
  if (!open.value) return;
  if (event.key === "ArrowDown") { event.preventDefault(); activeIndex.value = Math.min(activeIndex.value + 1, filtered.value.length - 1); }
  if (event.key === "ArrowUp") { event.preventDefault(); activeIndex.value = Math.max(activeIndex.value - 1, 0); }
  if (event.key === "Enter" && filtered.value[activeIndex.value]) { event.preventDefault(); choose(filtered.value[activeIndex.value]); }
  if (event.key === "Escape") { event.preventDefault(); open.value = false; }
}
function outside(event) { if (root.value && !root.value.contains(event.target)) open.value = false; }
onMounted(() => document.addEventListener("pointerdown", outside));
onBeforeUnmount(() => document.removeEventListener("pointerdown", outside));
</script>

<template>
  <div ref="root" class="dux-search-select" :class="{ open, disabled }" @keydown="keydown">
    <div class="dux-search-control" @click="show">
      <svg class="dux-search-icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="m16 16 4 4"/></svg>
      <input ref="searchInput" :value="displayValue" :placeholder="placeholder" :readonly="!open" :disabled="disabled" autocomplete="off" @input="query = $event.target.value" @focus="show" />
      <button v-if="modelValue && !disabled" class="dux-select-clear" type="button" aria-label="Clear selection" @click.stop="clear">×</button>
      <svg v-else class="dux-chevron" viewBox="0 0 24 24" aria-hidden="true"><path d="m7 10 5 5 5-5"/></svg>
    </div>
    <div v-if="open" class="dux-search-menu">
      <div class="dux-search-meta">{{ filtered.length }} options</div>
      <button v-for="(option, index) in filtered" :key="String(option[valueKey])" type="button" class="dux-search-option" :class="{ active: index === activeIndex, selected: String(option[valueKey]) === String(modelValue) }" @mouseenter="activeIndex = index" @click="choose(option)">
        <span><b>{{ option[labelKey] || option[valueKey] }}</b><small v-if="secondaryKey && option[secondaryKey]">{{ option[secondaryKey] }}</small></span>
        <svg v-if="String(option[valueKey]) === String(modelValue)" viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6"/></svg>
      </button>
      <div v-if="!filtered.length" class="dux-search-empty">No matching records</div>
      <button v-if="createLabel" type="button" class="dux-search-create" @click="emit('create', query); open = false"><span>＋</span>{{ createLabel }}</button>
    </div>
  </div>
</template>

<style scoped>
.dux-search-select{position:relative;width:100%;font-family:var(--font-ui)}
.dux-search-control{height:42px;padding:0 12px;display:flex;align-items:center;gap:9px;border:1px solid var(--border-strong);border-radius:var(--r-md);background:var(--bg-surface);box-shadow:var(--inset-hi);transition:border-color var(--dur-base) var(--ease),box-shadow var(--dur-base) var(--ease)}
.dux-search-select.open .dux-search-control{border-color:var(--iris);box-shadow:0 0 0 3px var(--iris-tint),var(--inset-hi)}
.dux-search-icon,.dux-chevron{width:15px;height:15px;fill:none;stroke:var(--text-muted);stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round;flex:0 0 auto}.dux-search-select.open .dux-search-icon{stroke:var(--iris)}
input{min-width:0!important;min-height:0!important;height:auto!important;padding:0!important;border:0!important;border-radius:0!important;box-shadow:none!important;background:transparent!important;flex:1;color:var(--text-primary)!important;font:var(--fw-regular) var(--fs-sm)/1.2 var(--font-ui)!important;cursor:pointer}input:focus{box-shadow:none!important}.open input{cursor:text}
.dux-select-clear{width:22px;height:22px;padding:0;border:0;border-radius:50%;background:var(--bg-sunken);color:var(--text-muted);cursor:pointer}
.dux-search-menu{position:absolute;z-index:1000;top:calc(100% + 6px);left:0;right:0;max-height:300px;overflow:auto;padding:6px;border:1px solid var(--border-strong);border-radius:var(--r-md);background:var(--bg-card);box-shadow:var(--shadow-pop),var(--inset-hi);animation:select-in .18s var(--spring)}
.dux-search-meta{padding:6px 9px;color:var(--text-muted);font-size:var(--fs-micro);text-transform:uppercase;letter-spacing:var(--ls-label)}
.dux-search-option{width:100%;min-height:38px;padding:8px 9px;display:flex;align-items:center;justify-content:space-between;gap:8px;border:0;border-radius:var(--r-sm);background:transparent;color:var(--text-primary);text-align:left;cursor:pointer;transition:background var(--dur-fast) var(--ease),transform var(--dur-fast) var(--spring)}
.dux-search-option:hover,.dux-search-option.active{background:var(--row-hover);transform:translateX(2px)}.dux-search-option.selected{color:var(--iris);background:var(--iris-tint)}
.dux-search-option span{display:block;min-width:0}.dux-search-option b{display:block;overflow:hidden;text-overflow:ellipsis;font-size:var(--fs-sm);font-weight:var(--fw-medium);white-space:nowrap}.dux-search-option small{display:block;margin-top:2px;color:var(--text-muted);font-size:var(--fs-micro);font-family:var(--font-mono)}
.dux-search-option svg{width:15px;height:15px;fill:none;stroke:currentColor;stroke-width:1.7;flex:0 0 auto}
.dux-search-empty{padding:18px 10px;color:var(--text-muted);font-size:var(--fs-sm);text-align:center}
.dux-search-create{position:sticky;bottom:0;width:100%;padding:10px 9px;display:flex;gap:8px;border:0;border-top:1px solid var(--border-subtle);background:var(--bg-card);color:var(--iris);font-size:var(--fs-sm);font-weight:var(--fw-medium);cursor:pointer}.dux-search-create:hover{background:var(--iris-tint)}
.disabled{opacity:.5;pointer-events:none}@keyframes select-in{from{opacity:0;transform:translateY(-5px) scale(.99)}to{opacity:1;transform:none}}
@media(prefers-reduced-motion:reduce){.dux-search-menu{animation:none}.dux-search-option{transition:none}}
</style>
