import { createApp } from "vue";
import App from "./App.vue";
import "./styles.css";
import "./dux-design-system/index.css";
import "./dux-overrides.css";
import { attachAutoCapitalize, detachAutoCapitalize } from "./auto-capitalize.js";

// The Frappe page loader is the single source of truth for the active UI
// version. Reading its data attribute prevents a rebuilt bundle from being
// rejected because a second hard-coded version was not updated.
export const version = typeof document !== "undefined"
  ? document.currentScript?.dataset?.cmrUi || "dev"
  : "dev";

let activeApp = null;

export function mount(element, options = {}) {
  if (!element) throw new Error("CMR Pipe Laying Master mount element is required");
  if (activeApp) activeApp.unmount();
  activeApp = createApp(App, options);
  activeApp.mount(element);
  attachAutoCapitalize(element);
  return activeApp;
}

export function unmount() {
  detachAutoCapitalize();
  if (!activeApp) return;
  activeApp.unmount();
  activeApp = null;
}

// Frappe loads this bundle dynamically, so publish the public API explicitly.
if (typeof window !== "undefined") {
  window.CMRPipeLayingMaster = { mount, unmount, version };
}
