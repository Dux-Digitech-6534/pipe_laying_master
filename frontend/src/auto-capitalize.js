// Capitalizes the first letter of every free-text input/textarea inside this
// app's own DOM subtree, live as the user types. Attached once at mount time
// on the app's root element (capture phase, so the correction lands before
// Vue's own v-model listener reads the value) rather than per-field, since
// this behaviour is meant to apply everywhere text is typed, not just Remarks.

const SKIP_INPUT_TYPES = ["number", "date", "time", "datetime-local", "month", "week", "checkbox", "radio", "file", "hidden", "color", "range"];

let attachedElement = null;

function shouldSkip(target) {
  const isTextArea = target instanceof HTMLTextAreaElement;
  const isTextInput = target instanceof HTMLInputElement && !SKIP_INPUT_TYPES.includes(target.type);
  if (!isTextArea && !isTextInput) return true;
  if (target.disabled || target.readOnly) return true;
  return false;
}

function handleInput(event) {
  const target = event.target;
  if (shouldSkip(target)) return;
  const value = target.value;
  if (!value) return;
  const first = value[0];
  const upper = first.toUpperCase();
  if (first === upper) return;
  const selStart = target.selectionStart;
  const selEnd = target.selectionEnd;
  target.value = upper + value.slice(1);
  if (selStart !== null && selEnd !== null) target.setSelectionRange(selStart, selEnd);
}

export function attachAutoCapitalize(element) {
  if (!element || attachedElement) return;
  element.addEventListener("input", handleInput, true);
  attachedElement = element;
}

export function detachAutoCapitalize() {
  if (attachedElement) attachedElement.removeEventListener("input", handleInput, true);
  attachedElement = null;
}
