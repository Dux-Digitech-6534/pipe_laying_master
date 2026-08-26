<script setup>
import { computed, onMounted, ref } from "vue";
import "../modern-form.css";

const props = defineProps({ sourceName: { type: String, default: "" }, recordName: { type: String, default: "" } });
const emit = defineEmits(["close"]);
const loading = ref(true);
const saving = ref(false);
const error = ref("");
const model = ref({ items: [], taxes: [] });
const documentInfo = ref(null);
const activeRecordName = ref(props.recordName || "");
const sourceName = ref(props.sourceName || "");
const isReadOnly = computed(() => Boolean(documentInfo.value && documentInfo.value.docstatus !== 0));
const statusLabel = computed(() => documentInfo.value?.docstatus === 0 ? "Draft" : documentInfo.value?.docstatus === 1 ? "Submitted" : "Cancelled");
const heading = computed(() => activeRecordName.value ? `${isReadOnly.value ? "View" : "Edit"} Purchase Return` : "New Purchase Return");
const totalReturnQty = computed(() => (model.value.items || []).reduce((sum, row) => sum + (Number(row.return_qty) || 0), 0));

function call(method, args = {}) {
  return new Promise((resolve, reject) => window.frappe.call({ method, args, callback: r => resolve(r.message), error: reject }));
}
function applyResult(result) {
  model.value = result || { items: [], taxes: [] };
  documentInfo.value = result?._document || null;
  activeRecordName.value = result?.record_name || documentInfo.value?.name || activeRecordName.value;
  sourceName.value = result?.source_name || sourceName.value;
}
async function load() {
  loading.value = true; error.value = "";
  try {
    const result = activeRecordName.value
      ? await call("cmr_pipe_laying_master.api.entries.get_purchase_return_document", { record_name: activeRecordName.value })
      : await call("cmr_pipe_laying_master.api.entries.get_purchase_return_preview", { purchase_receipt: sourceName.value });
    applyResult(result);
  } catch (e) { error.value = "Purchase Return details could not be loaded."; }
  finally { loading.value = false; }
}
function normalizeQty(row) {
  const qty = Number(row.return_qty);
  row.return_qty = Number.isFinite(qty) ? Math.max(0, Math.min(qty, Number(row.available_qty) || 0)) : 0;
}
async function save(action) {
  error.value = "";
  if (!model.value.items.some(row => Number(row.return_qty) > 0)) {
    error.value = "Enter Return Qty for at least one item.";
    return;
  }
  saving.value = true;
  try {
    const result = await call("cmr_pipe_laying_master.api.entries.save_purchase_return", {
      purchase_receipt: sourceName.value,
      payload: JSON.stringify({ posting_date: model.value.posting_date, remarks: model.value.remarks, items: model.value.items }),
      action,
      record_name: activeRecordName.value,
    });
    applyResult(result);
    window.frappe.show_alert({ message: `${result.record_name} ${action === "submit" ? "submitted" : "saved as Draft"}`, indicator: "green" }, 7);
  } catch (e) { error.value = "Purchase Return could not be saved. Check quantities, stock, permissions and linked Purchase Receipt."; }
  finally { saving.value = false; }
}
function confirmAction(message) {
  return new Promise(resolve => window.frappe?.confirm ? window.frappe.confirm(message, () => resolve(true), () => resolve(false)) : resolve(window.confirm(message)));
}
async function runAction(action) {
  const messages = { delete: "Delete this Draft Purchase Return?", cancel: "Cancel this Purchase Return? ERPNext will reverse its stock effect." };
  if (messages[action] && !await confirmAction(messages[action])) return;
  saving.value = true; error.value = "";
  try {
    const result = await call("cmr_pipe_laying_master.api.entries.run_entry_action", { entry_type: "material-inward", record_name: activeRecordName.value, action });
    if (result.deleted) { emit("close"); return; }
    if (["amend", "duplicate"].includes(action)) activeRecordName.value = result.name;
    await load();
    window.frappe.show_alert({ message: `Purchase Return ${action} completed`, indicator: "green" }, 6);
  } catch (e) { error.value = `Purchase Return ${action} could not be completed.`; }
  finally { saving.value = false; }
}
function printDocument() {
  const query = new URLSearchParams({ doctype: "Purchase Receipt", name: activeRecordName.value, format: "Standard", no_letterhead: "0", trigger_print: "1" });
  window.open(`/printview?${query.toString()}`, "_blank", "noopener");
}
onMounted(load);
</script>

<template>
  <section class="cmr-modern-form cmr-purchase-return-form">
    <div class="cmr-form-toolbar">
      <div><button class="cmr-back-link" type="button" @click="emit('close')">← Back to Material Inward</button><h2>{{ heading }}</h2><p>Native ERPNext Purchase Receipt Return against <b>{{ sourceName }}</b></p></div>
      <div class="cmr-form-actions">
        <template v-if="!documentInfo || documentInfo.docstatus === 0">
          <button v-if="documentInfo?.can_delete" class="cmr-button danger" type="button" :disabled="saving" @click="runAction('delete')">Delete</button>
          <button class="cmr-button" type="button" :disabled="saving" @click="save('draft')">Save Draft</button>
          <button class="cmr-button primary" type="button" :disabled="saving" @click="save('submit')">Save & Submit</button>
        </template>
        <template v-else>
          <button class="cmr-button" type="button" @click="printDocument">Print</button>
          <button v-if="documentInfo.can_create" class="cmr-button" type="button" :disabled="saving" @click="runAction('duplicate')">Duplicate</button>
          <button v-if="documentInfo.docstatus === 1 && documentInfo.can_cancel" class="cmr-button danger" type="button" :disabled="saving" @click="runAction('cancel')">Cancel</button>
          <button v-if="documentInfo.docstatus === 2 && documentInfo.can_create" class="cmr-button primary" type="button" :disabled="saving" @click="runAction('amend')">Amend</button>
        </template>
      </div>
    </div>
    <div class="cmr-native-note"><span>♦</span>This uses ERPNext's native Purchase Receipt Return mapper, stock ledger, taxes and submit/cancel lifecycle.</div>
    <div v-if="documentInfo" class="cmr-document-state"><div><b>{{ documentInfo.name }}</b><small>Purchase Receipt Return • {{ documentInfo.return_against }}</small></div><span class="cmr-status-pill" :class="`status-${documentInfo.docstatus}`">{{ statusLabel }}</span></div>
    <div v-if="loading" class="cmr-form-message">Loading native return details…</div>
    <div v-if="error" class="cmr-form-message error">{{ error }}</div>

    <fieldset v-if="!loading" class="cmr-document-fields" :disabled="isReadOnly">
      <div class="cmr-form-section">
        <div class="cmr-section-title"><span>1</span><div><b>Original Material Inward</b><small>Auto-fetched from submitted Purchase Receipt</small></div></div>
        <div class="cmr-form-grid">
          <label><span>Posting Date *</span><input v-model="model.posting_date" type="date" /></label>
          <label><span>Supplier</span><input :value="model.supplier" readonly /></label>
          <label><span>Company</span><input :value="model.company" readonly /></label>
          <label><span>Project</span><input :value="model.project" readonly /></label>
          <label><span>Site</span><input :value="model.site" readonly /></label>
          <label><span>Receiving Warehouse</span><input :value="model.warehouse" readonly /></label>
        </div>
      </div>

      <div class="cmr-form-section">
        <div class="cmr-section-title"><span>2</span><div><b>Return Items</b><small>Select partial or full quantities. ERPNext validates available return quantity again on the server.</small></div></div>
        <div class="cmr-return-table-wrap"><table class="cmr-return-table"><thead><tr><th>Item</th><th>Warehouse</th><th>UOM</th><th>Rate</th><th>Received Qty</th><th>Already Returned</th><th>Available Qty</th><th>Return Qty</th></tr></thead><tbody><tr v-for="row in model.items" :key="row.source_item"><td><b>{{ row.item_code }}</b><small>{{ row.item_name }}</small></td><td>{{ row.warehouse }}</td><td>{{ row.uom }}</td><td>{{ Number(row.rate).toFixed(2) }}</td><td>{{ row.received_qty }}</td><td>{{ row.already_returned_qty }}</td><td>{{ row.available_qty }}</td><td><input v-model.number="row.return_qty" type="number" min="0" :max="row.available_qty" step="0.001" @change="normalizeQty(row)" /></td></tr></tbody></table></div>
        <div class="cmr-return-total">Total Return Qty <b>{{ totalReturnQty.toFixed(3) }}</b></div>
      </div>

      <div v-if="model.taxes?.length" class="cmr-form-section">
        <div class="cmr-section-title"><span>3</span><div><b>Taxes / GST</b><small>Copied and recalculated by ERPNext native return logic</small></div></div>
        <div class="cmr-return-tax-list"><div v-for="tax in model.taxes" :key="`${tax.description}-${tax.rate}`"><span>{{ tax.description }} ({{ tax.charge_type }})</span><b>{{ tax.rate }}% · {{ Number(tax.tax_amount).toFixed(2) }}</b></div></div>
      </div>

      <div class="cmr-form-section"><div class="cmr-section-title"><span>✓</span><div><b>Remarks</b><small>Optional return note</small></div></div><label class="cmr-return-remarks"><span>Remarks</span><textarea v-model="model.remarks" rows="3" /></label></div>
    </fieldset>
  </section>
</template>