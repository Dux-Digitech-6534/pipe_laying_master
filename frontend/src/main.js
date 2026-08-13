import { createApp } from "vue";
import App from "./App.vue";
import "./styles.css";
import "./dux-design-system/index.css";
import "./dux-overrides.css";

export const version = "11";

let activeApp = null;

export function mount(element, options = {}) {
  if (!element) throw new Error("CMR Pipe Laying Master mount element is required");
  if (activeApp) activeApp.unmount();
  activeApp = createApp(App, options);
  activeApp.mount(element);
  return activeApp;
}

export function unmount() {
  if (!activeApp) return;
  activeApp.unmount();
  activeApp = null;
}

// Frappe loads this bundle dynamically, so publish the public API explicitly.
if (typeof window !== "undefined") {
  window.CMRPipeLayingMaster = { mount, unmount, version };
}
