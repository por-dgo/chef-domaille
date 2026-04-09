const state = {
  recipes: [],
  selectedRecipe: null,
  bundle: null,
  currentStepIndex: 0,
  dirty: false,
  savedSnapshot: null,
  exportMode: false,
  exportSelected: new Set(),
  consumables: { Film: [], Pad: [], Lubricant: [] },
  savedConsumables: null,
  removableDrives: [],
};

function el(id) { return document.getElementById(id); }

function showToast(message, isError = false, timeoutMs = 4500) {
  const container = el("toastContainer");
  if (!container) return;
  const toast = document.createElement("div");
  toast.className = `toast ${isError ? "toast-error" : "toast-ok"}`;
  toast.textContent = message;
  container.appendChild(toast);
  window.setTimeout(() => {
    toast.remove();
  }, timeoutMs);
}

function status(msg, isError = false) {
  showToast(msg, isError);
}

function showImportToasts(data) {
  const added = data.added || [];
  const updated = data.updated || [];
  const settingsAdded = data.settings_added || {};
  const messages = [];
  const allChanged = [...added.map((n) => `New recipe: ${n}`), ...updated.map((n) => `Updated recipe: ${n}`)];

  if (allChanged.length === 0) {
    messages.push("No changes \u2014 all recipes already up to date.");
  } else if (allChanged.length <= 6) {
    messages.push(...allChanged);
  } else {
    const names = [...added, ...updated];
    messages.push(`Imported ${names.length} recipes: ${names.join(", ")}`);
  }

  const settingsParts = [];
  for (const [category, values] of Object.entries(settingsAdded)) {
    if (values.length) {
      const quoted = values.map((v) => `"${v}"`).join(", ");
      settingsParts.push(`${category}: added ${quoted}`);
    }
  }
  if (settingsParts.length) {
    messages.push(`Settings \u2014 ${settingsParts.join("; ")}`);
  }

  // Longer timeout for bulk summary so there's time to read the list
  const total = added.length + updated.length;
  const timeout = total > 6 ? 4500 + total * 250 : undefined;

  messages.forEach((msg, i) => {
    window.setTimeout(() => showToast(msg, false, timeout), i * 100);
  });
}

function settingsStatus(msg, isError = false) {
  showToast(msg, isError);
}

function confirmDialog(message) {
  const overlay = el("confirmModal");
  const messageBox = el("confirmMessage");
  const okBtn = el("confirmOkBtn");
  const cancelBtn = el("confirmCancelBtn");
  if (!overlay || !messageBox || !okBtn || !cancelBtn) {
    return Promise.resolve(window.confirm(message));
  }

  overlay.hidden = false;
  messageBox.textContent = message;
  okBtn.focus();

  return new Promise((resolve) => {
    const close = (result) => {
      overlay.hidden = true;
      okBtn.removeEventListener("click", onOk);
      cancelBtn.removeEventListener("click", onCancel);
      overlay.removeEventListener("click", onOverlay);
      document.removeEventListener("keydown", onEscape);
      resolve(result);
    };

    const onOk = () => close(true);
    const onCancel = () => close(false);
    const onOverlay = (event) => {
      if (event.target === overlay) close(false);
    };
    const onEscape = (event) => {
      if (event.key === "Escape") close(false);
    };

    okBtn.addEventListener("click", onOk);
    cancelBtn.addEventListener("click", onCancel);
    overlay.addEventListener("click", onOverlay);
    document.addEventListener("keydown", onEscape);
  });
}

function getSelectedRecipeNames() {
  if (state.exportMode) return Array.from(state.exportSelected);
  if (state.selectedRecipe) return [state.selectedRecipe];
  return [];
}

function snapshotBundle() {
  if (!state.bundle) return null;
  return JSON.stringify({
    recipe_name: state.bundle.recipe_name,
    recipe_data: state.bundle.recipe_data,
    steps: state.bundle.steps,
  });
}

function checkDirty() {
  if (!state.bundle) { setDirty(false); return; }
  bindCurrentStepInputs();
  updateBundleFromHeader();
  const current = snapshotBundle();
  setDirty(current !== state.savedSnapshot);
}

function setDirty(isDirty) {
  state.dirty = isDirty;
  const saveBtn = el("saveBtn");
  const resetBtn = el("resetBtn");
  if (saveBtn) saveBtn.disabled = !isDirty;
  if (resetBtn) resetBtn.disabled = !isDirty;
  updateEditorSubtitle();
}

function showEditor() {
  const placeholder = el("editorPlaceholder");
  const body = el("editorBody");
  if (placeholder) placeholder.hidden = true;
  if (body) body.hidden = false;
}

function hideEditor() {
  const placeholder = el("editorPlaceholder");
  const body = el("editorBody");
  if (placeholder) placeholder.hidden = false;
  if (body) body.hidden = true;
  state.bundle = null;
  state.selectedRecipe = null;
  setDirty(false);
  updateEditorSubtitle();
}

function toggleSettings() {
  const btn = el("settingsToggleBtn");
  const body = el("settingsBody");
  if (!btn || !body) return;
  const expanded = btn.getAttribute("aria-expanded") === "true";
  btn.setAttribute("aria-expanded", String(!expanded));
  btn.title = expanded ? "Expand settings" : "Collapse settings";
  body.hidden = expanded;
  const section = body.closest(".collapsible-panel");
  if (section) section.classList.toggle("collapsed", expanded);
}

function closeAccordions() {
  const exp = el("exportAccordion");
  const imp = el("importAccordion");
  if (exp) exp.hidden = true;
  if (imp) imp.hidden = true;
  if (state.exportMode) {
    state.exportMode = false;
    state.exportSelected.clear();
    refreshRecipes();
  }
}

function renderDriveHints() {}

function refreshExportUi() {
  const type = el("exportTypeSelect")?.value || "book";
  const thumbRow = el("exportThumbRow");
  const bookRow = el("exportBookRow");
  if (thumbRow) thumbRow.hidden = type !== "thumb";
  if (bookRow) bookRow.hidden = type !== "book";
}

function refreshImportUi() {
  const type = el("importTypeSelect")?.value || "book";
  const thumbRow = el("importThumbRow");
  const bookRow = el("importBookRow");
  if (thumbRow) thumbRow.hidden = type !== "thumb";
  if (bookRow) bookRow.hidden = type !== "book";
}

function prefillDrivePaths() {
  if (!state.removableDrives.length) return;
  const drive = state.removableDrives[0];
  const exportPath = el("exportThumbPath");
  const importPath = el("importThumbPath");
  if (exportPath && !exportPath.value) exportPath.value = drive;
  if (importPath && !importPath.value) importPath.value = drive;
}

function openExportAccordion() {
  closeAccordions();
  state.exportMode = true;
  state.exportSelected = new Set(state.recipes);
  loadRemovableDrives().then(() => { renderDriveHints(); prefillDrivePaths(); });
  refreshExportUi();
  refreshRecipes();
  const acc = el("exportAccordion");
  if (acc) acc.hidden = false;
}

function openImportAccordion() {
  closeAccordions();
  loadRemovableDrives().then(() => { renderDriveHints(); prefillDrivePaths(); });
  refreshImportUi();
  const acc = el("importAccordion");
  if (acc) acc.hidden = false;
}

async function loadRemovableDrives() {
  try {
    const data = await api("/api/system/removable-drives");
    state.removableDrives = data.drives || [];
  } catch {
    state.removableDrives = [];
  }
}

async function downloadRecipeBook(selectedRecipes, fileName) {
  const response = await fetch("/api/transfer/export/book", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ selected_recipes: selectedRecipes }),
  });
  if (!response.ok) {
    let errorText = "Recipe book export failed";
    try {
      const data = await response.json();
      errorText = data.error || errorText;
    } catch {
      // ignore parse errors
    }
    throw new Error(errorText);
  }

  const blob = await response.blob();
  const safeName = (fileName || "recipe-book.chef").trim() || "recipe-book.chef";

  if (window.showSaveFilePicker) {
    try {
      const handle = await window.showSaveFilePicker({
        suggestedName: safeName,
        types: [{ description: "Chef Recipe Book", accept: { "application/octet-stream": [".chef"] } }],
      });
      const writable = await handle.createWritable();
      await writable.write(blob);
      await writable.close();
      return;
    } catch {
      // Fall through to anchor download.
    }
  }

  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = safeName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(objectUrl);
}

async function runExport() {
  const type = el("exportTypeSelect").value;

  if (type === "thumb") {
    const destination = el("exportThumbPath").value.trim();
    if (!destination) throw new Error("Folder path is required");
    await transfer("/api/transfer/export/thumb", {
      destination_path: destination,
      selected_recipes: getSelectedRecipeNames(),
    });
  } else {
    await downloadRecipeBook(getSelectedRecipeNames(), el("exportBookName").value);
    status("Recipe book exported");
  }
  closeAccordions();
}

async function runImport() {
  const type = el("importTypeSelect").value;
  let data;

  if (type === "thumb") {
    const source = el("importThumbPath").value.trim();
    if (!source) throw new Error("Folder path is required");
    data = await api("/api/transfer/import/thumb", "POST", {
      source_path: source,
      selected_recipes: [],
      overwrite: true,
    });
  } else {
    const fileInput = el("importBookFile");
    const file = fileInput?.files?.[0];
    if (!file) throw new Error("Select a .chef file to import");
    const formData = new FormData();
    formData.append("file", file);
    const response = await fetch("/api/transfer/import/book", {
      method: "POST",
      body: formData,
    });
    data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.error || "Import failed");
    }
  }

  await refreshRecipes();
  await loadConsumables();
  showImportToasts(data);
  closeAccordions();
}

function setActiveTab(tabName) {
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabPanels = document.querySelectorAll(".tab-panel");

  tabButtons.forEach((button) => {
    const isActive = button.dataset.tab === tabName;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-selected", isActive ? "true" : "false");
  });

  tabPanels.forEach((panel) => {
    const isActive = panel.dataset.tabPanel === tabName;
    panel.classList.toggle("active", isActive);
    panel.hidden = !isActive;
  });
}

function wireTabs() {
  const tabButtons = document.querySelectorAll(".tab-btn");
  tabButtons.forEach((button) => {
    button.addEventListener("click", () => {
      setActiveTab(button.dataset.tab);
    });
  });
}

async function api(path, method = "GET", body = null) {
  const res = await fetch(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : null,
  });
  const data = await res.json();
  if (!res.ok) throw new Error((data.errors || ["request failed"]).join("; "));
  return data;
}

async function loadConsumables() {
  try {
    const data = await api("/api/settings/consumables");
    state.consumables = data;
    loadSettingsEditor();
    state.savedConsumables = JSON.stringify(state.consumables);
    populateSelectDropdowns();
    updateSettingsSubtitle();
  } catch (e) {
    console.error("Failed to load consumables:", e);
  }
}

function populateSelectDropdowns() {
  for (const [category, options] of Object.entries(state.consumables)) {
    const combo = el(`combo${category}`);
    if (!combo) continue;
    const list = combo.querySelector(".combo-list");
    if (!list) continue;
    list.innerHTML = "";
    for (const opt of options) {
      const li = document.createElement("li");
      li.textContent = opt;
      li.addEventListener("mousedown", (e) => {
        e.preventDefault(); // keep focus on input
        const input = combo.querySelector("input");
        input.value = opt;
        list.hidden = true;
        input.dispatchEvent(new Event("input", { bubbles: true }));
      });
      list.appendChild(li);
    }
  }
}

function setSelectValue(id, value) {
  const input = el(id);
  if (!input) return;
  input.value = value || "";
}

function wireComboBoxes() {
  for (const category of ["Film", "Pad", "Lubricant"]) {
    const combo = el(`combo${category}`);
    if (!combo) continue;
    const input = combo.querySelector("input");
    const toggle = combo.querySelector(".combo-toggle");
    const list = combo.querySelector(".combo-list");

    const showList = () => { list.hidden = false; };
    const hideList = () => { list.hidden = true; };

    toggle.addEventListener("mousedown", (e) => {
      e.preventDefault();
      if (list.hidden) { showList(); input.focus(); }
      else { hideList(); }
    });

    input.addEventListener("focus", showList);
    input.addEventListener("blur", () => {
      // Small delay so mousedown on li fires first
      setTimeout(hideList, 150);
    });
  }
}

function uniqueValues(items) {
  const seen = new Set();
  const result = [];
  for (const raw of items || []) {
    const value = String(raw || "").trim();
    if (!value) continue;
    const key = value.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(value);
  }
  return result;
}

function reorderList(list, fromIndex, toIndex) {
  const next = [...list];
  const [moved] = next.splice(fromIndex, 1);
  next.splice(toIndex, 0, moved);
  return next;
}

function renderOptionChips(kind) {
  const idPrefix = kind.toLowerCase();
  const container = el(`${idPrefix}OptionList`);
  if (!container) return;
  container.innerHTML = "";
  const values = state.consumables[kind] || [];
  values.forEach((value, index) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.draggable = true;
    chip.dataset.index = String(index);
    chip.textContent = value;

    chip.addEventListener("dragstart", (event) => {
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("text/plain", String(index));
      chip.classList.add("chip-dragging");
    });

    chip.addEventListener("dragend", () => {
      chip.classList.remove("chip-dragging");
      container.querySelectorAll(".chip-drop-target").forEach((node) => node.classList.remove("chip-drop-target"));
    });

    chip.addEventListener("dragover", (event) => {
      event.preventDefault();
      chip.classList.add("chip-drop-target");
    });

    chip.addEventListener("dragleave", () => {
      chip.classList.remove("chip-drop-target");
    });

    chip.addEventListener("drop", (event) => {
      event.preventDefault();
      chip.classList.remove("chip-drop-target");
      const fromIndex = Number.parseInt(event.dataTransfer.getData("text/plain"), 10);
      const toIndex = index;
      if (!Number.isInteger(fromIndex) || fromIndex === toIndex) return;
      state.consumables[kind] = reorderList(state.consumables[kind] || [], fromIndex, toIndex);
      renderOptionChips(kind);
      populateSelectDropdowns();
      updateSettingsSubtitle();
    });

    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "chip-remove";
    removeBtn.textContent = "x";
    removeBtn.setAttribute("aria-label", `Remove ${value}`);
    removeBtn.addEventListener("click", () => {
      state.consumables[kind] = values.filter((item) => item !== value);
      renderOptionChips(kind);
      populateSelectDropdowns();
      updateSettingsSubtitle();
    });

    chip.appendChild(removeBtn);
    container.appendChild(chip);
  });
}

function addOption(kind) {
  const idPrefix = kind.toLowerCase();
  const input = el(`${idPrefix}OptionInput`);
  if (!input) return;
  const next = input.value.trim();
  if (!next) return;
  const merged = [...(state.consumables[kind] || []), next];
  state.consumables[kind] = uniqueValues(merged);
  input.value = "";
  renderOptionChips(kind);
  populateSelectDropdowns();
  updateSettingsSubtitle();
}

function loadSettingsEditor() {
  state.consumables = {
    Film: uniqueValues(state.consumables.Film || []),
    Pad: uniqueValues(state.consumables.Pad || []),
    Lubricant: uniqueValues(state.consumables.Lubricant || []),
  };
  renderOptionChips("Film");
  renderOptionChips("Pad");
  renderOptionChips("Lubricant");
}

async function saveSettings() {
  try {
    const consumables = {
      Film: uniqueValues(state.consumables.Film || []),
      Pad: uniqueValues(state.consumables.Pad || []),
      Lubricant: uniqueValues(state.consumables.Lubricant || []),
    };
    await api("/api/settings/consumables", "PUT", consumables);
    state.consumables = consumables;
    state.savedConsumables = JSON.stringify(state.consumables);
    populateSelectDropdowns();
    loadSettingsEditor();
    updateSettingsSubtitle();
    settingsStatus("Settings saved!");
  } catch (e) {
    settingsStatus(e.message, true);
  }
}

function updateSettingsSubtitle() {
  const sub = el("settingsSubtitle");
  if (!sub) return;
  if (!state.savedConsumables) { sub.textContent = ""; return; }
  const current = JSON.stringify(state.consumables);
  sub.textContent = current !== state.savedConsumables ? "Edited" : "";
}

function wireSettingsEditor() {
  ["Film", "Pad", "Lubricant"].forEach((kind) => {
    const idPrefix = kind.toLowerCase();
    const addBtn = el(`add${kind}OptionBtn`);
    const input = el(`${idPrefix}OptionInput`);
    if (addBtn) {
      addBtn.addEventListener("click", () => addOption(kind));
    }
    if (input) {
      input.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
          event.preventDefault();
          addOption(kind);
        }
      });
    }
  });
}

function defaultStep() {
  return {
    rRecipeStepTime: "25",
    rRecipeStepSpeed: "110",
    rRecipeStepSpeedRamp: "1",
    rRecipeStepPressure: "12",
    rRecipeStepPressureRamp: "1",
    rRecipeStepFCI: "0",
    rRecipeStepLowerSpeedLimit: "10",
    rRecipeStepUpperSpeedLimit: "10",
    rRecipeStepLowerPressureLimit: "0.5",
    rRecipeStepUpperPressureLimit: "0.5",
    rRecipeStepFixtureWeight: "0",
    intRecipeStepOpCode: "300",
    strRecipeStepFilm: "Brown 5um",
    strRecipeStepLubricant: "DI Water",
    strRecipeStepPad: "70 Duro Violet",
    strRecipeStepDescription1: "",
    strRecipeStepDescription2: "",
    rRecipeStepSpeedRampDn: "1",
    rRecipeStepPressureRampDn: "1",
  };
}

function bindCurrentStepInputs() {
  if (!state.bundle) return;
  const step = state.bundle.steps[state.currentStepIndex];
  step.rRecipeStepTime = el("stepTime").value;
  step.rRecipeStepSpeed = el("stepSpeed").value;
  step.rRecipeStepSpeedRamp = el("stepSpeedRamp").value;
  step.rRecipeStepPressure = el("stepPressure").value;
  step.rRecipeStepPressureRamp = el("stepPressureRamp").value;
  step.rRecipeStepSpeedRampDn = el("stepSpeedRampDn").value;
  step.rRecipeStepPressureRampDn = el("stepPressureRampDn").value;
  step.strRecipeStepFilm = el("stepFilm").value;
  step.strRecipeStepPad = el("stepPad").value;
  step.strRecipeStepLubricant = el("stepLubricant").value;
  step.strRecipeStepDescription1 = el("stepNote1").value;
  step.strRecipeStepDescription2 = el("stepNote2").value;
}

function renderCurrentStep() {
  if (!state.bundle) return;
  const step = state.bundle.steps[state.currentStepIndex];
  el("stepTime").value = step.rRecipeStepTime || "";
  el("stepSpeed").value = step.rRecipeStepSpeed || "";
  el("stepSpeedRamp").value = step.rRecipeStepSpeedRamp || "";
  el("stepPressure").value = step.rRecipeStepPressure || "";
  el("stepPressureRamp").value = step.rRecipeStepPressureRamp || "";
  el("stepSpeedRampDn").value = step.rRecipeStepSpeedRampDn || "";
  el("stepPressureRampDn").value = step.rRecipeStepPressureRampDn || "";
  setSelectValue("stepFilm", step.strRecipeStepFilm || "");
  setSelectValue("stepPad", step.strRecipeStepPad || "");
  setSelectValue("stepLubricant", step.strRecipeStepLubricant || "");
  el("stepNote1").value = step.strRecipeStepDescription1 || "";
  el("stepNote2").value = step.strRecipeStepDescription2 || "";
  renderStepTabs();
  updatePressurePerContact();
}

function updateBundleFromHeader() {
  if (!state.bundle) return;
  state.bundle.recipe_name = el("recipeName").value.trim();
  state.bundle.recipe_data.strRecipeDescription = el("recipeDescription").value;
  state.bundle.recipe_data.intRecipeQty = el("recipeQty").value;
  state.bundle.recipe_data.intRecipeNoOfSteps = String(state.bundle.steps.length);
}

function updatePressurePerContact() {
  const qty = parseFloat(el("recipeQty")?.value);
  const pressure = parseFloat(el("stepPressure")?.value);
  const qtySpan = el("qtyPpcLine");
  const pressureSpan = el("pressurePpcLine");
  let text = "";
  if (qty > 0 && pressure >= 0 && !isNaN(qty) && !isNaN(pressure)) {
    text = `Pressure per contact: ${(pressure / qty).toFixed(2)} lbs`;
  }
  if (qtySpan) qtySpan.textContent = text;
  if (pressureSpan) pressureSpan.textContent = text;
}

function renderBundleHeader() {
  if (!state.bundle) return;
  el("recipeName").value = state.bundle.recipe_name;
  el("recipeDescription").value = state.bundle.recipe_data.strRecipeDescription || "";
  el("recipeQty").value = state.bundle.recipe_data.intRecipeQty || "";
  updatePressurePerContact();
}

function updateEditorSubtitle() {
  const sub = el("editorSubtitle");
  if (!sub) return;
  if (!state.bundle) { sub.textContent = ""; return; }
  const name = state.bundle.recipe_name || "Untitled";
  const dirty = state.dirty ? " \u2022 Edited" : "";
  sub.textContent = `${name}${dirty}`;
}

function renderStepTabs() {
  const container = el("stepTabs");
  if (!container || !state.bundle) return;
  container.innerHTML = "";
  const canRemove = state.bundle.steps.length > 1;
  state.bundle.steps.forEach((_, i) => {
    const tab = document.createElement("button");
    tab.type = "button";
    tab.className = `step-tab${i === state.currentStepIndex ? " active" : ""}`;
    tab.setAttribute("role", "tab");
    tab.setAttribute("aria-selected", i === state.currentStepIndex ? "true" : "false");

    const label = document.createElement("span");
    label.textContent = `Step ${i + 1}`;
    tab.appendChild(label);

    if (canRemove) {
      const closeBtn = document.createElement("span");
      closeBtn.className = "step-tab-close";
      closeBtn.textContent = "\u00d7";
      closeBtn.setAttribute("aria-label", `Remove step ${i + 1}`);
      closeBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        removeStep(i);
      });
      tab.appendChild(closeBtn);
    }

    tab.addEventListener("click", () => switchToStep(i));
    container.appendChild(tab);
  });
}

function switchToStep(index) {
  if (!state.bundle) return;
  bindCurrentStepInputs();
  state.currentStepIndex = Math.max(0, Math.min(index, state.bundle.steps.length - 1));
  renderCurrentStep();
}

function addStep() {
  if (!state.bundle) return;
  if (state.bundle.steps.length >= 10) {
    showToast("Maximum 10 steps", true);
    return;
  }
  bindCurrentStepInputs();
  state.bundle.steps.push(defaultStep());
  state.bundle.recipe_data.intRecipeNoOfSteps = String(state.bundle.steps.length);
  state.currentStepIndex = state.bundle.steps.length - 1;
  renderCurrentStep();
  checkDirty();
}

async function removeStep(index) {
  if (!state.bundle || state.bundle.steps.length <= 1) return;
  const confirmed = await confirmDialog(`Remove Step ${index + 1}?`);
  if (!confirmed) return;
  bindCurrentStepInputs();
  state.bundle.steps.splice(index, 1);
  state.bundle.recipe_data.intRecipeNoOfSteps = String(state.bundle.steps.length);
  if (state.currentStepIndex >= state.bundle.steps.length) {
    state.currentStepIndex = state.bundle.steps.length - 1;
  }
  renderCurrentStep();
  checkDirty();
}

async function refreshRecipes() {
  const data = await api("/api/recipes");
  state.recipes = data.recipes;
  const list = el("recipeList");
  list.innerHTML = "";
  for (const name of state.recipes) {
    const li = document.createElement("li");

    if (state.exportMode) {
      const isChecked = state.exportSelected.has(name);
      li.classList.toggle("export-selected", isChecked);
      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.checked = isChecked;
      cb.addEventListener("change", () => {
        if (cb.checked) state.exportSelected.add(name);
        else state.exportSelected.delete(name);
        li.classList.toggle("export-selected", cb.checked);
      });
      const span = document.createElement("span");
      span.textContent = name;
      li.appendChild(cb);
      li.appendChild(span);
      li.addEventListener("click", (e) => {
        if (e.target === cb) return;
        cb.checked = !cb.checked;
        cb.dispatchEvent(new Event("change"));
      });
    } else {
      if (name === state.selectedRecipe) li.classList.add("active");
      li.textContent = name;
      li.addEventListener("click", () => loadRecipe(name));
    }

    list.appendChild(li);
  }
}

async function loadRecipe(name) {
  const data = await api(`/api/recipes/${encodeURIComponent(name)}`);
  state.selectedRecipe = name;
  state.bundle = {
    recipe_name: data.recipe_name,
    recipe_data: data.recipe_data,
    steps: data.steps,
  };
  state.currentStepIndex = 0;
  state.savedSnapshot = snapshotBundle();
  showEditor();
  renderBundleHeader();
  renderCurrentStep();
  setDirty(false);
  refreshRecipes();
}

function newRecipe() {
  state.bundle = {
    recipe_name: "new_recipe",
    recipe_data: {
      strRecipeDescription: "new recipe",
      intRecipeNoOfSteps: "1",
      intRecipeQty: "24",
      intRecipeReworkStep: "1",
    },
    steps: [defaultStep()],
  };
  state.selectedRecipe = null;
  state.currentStepIndex = 0;
  state.savedSnapshot = null;
  showEditor();
  renderBundleHeader();
  renderCurrentStep();
  setDirty(true);
}

async function saveRecipe() {
  if (!state.bundle) return;
  bindCurrentStepInputs();
  updateBundleFromHeader();
  const name = state.bundle.recipe_name;
  if (!name) {
    status("Recipe name is required", true);
    return;
  }
  // Ensure hidden fields have defaults
  const defaults = defaultStep();
  const hiddenKeys = [
    "rRecipeStepFCI", "rRecipeStepLowerSpeedLimit", "rRecipeStepUpperSpeedLimit",
    "rRecipeStepLowerPressureLimit", "rRecipeStepUpperPressureLimit",
    "rRecipeStepFixtureWeight", "intRecipeStepOpCode",
    "strRecipeStepDescription1", "strRecipeStepDescription2",
  ];
  for (const step of state.bundle.steps) {
    for (const key of hiddenKeys) {
      if (!(key in step) || step[key] === undefined || step[key] === null) step[key] = defaults[key] || "";
    }
  }
  // Ensure recipe-level defaults
  if (!state.bundle.recipe_data.intRecipeReworkStep) {
    state.bundle.recipe_data.intRecipeReworkStep = "1";
  }
  await api(`/api/recipes/${encodeURIComponent(name)}`, "PUT", {
    recipe_data: state.bundle.recipe_data,
    steps: state.bundle.steps,
  });
  state.selectedRecipe = name;
  state.savedSnapshot = snapshotBundle();
  setDirty(false);
  await refreshRecipes();
  status(`Saved ${name}`);
}

async function deleteRecipe() {
  const name = el("recipeName").value.trim();
  if (!name) return;
  const confirmed = await confirmDialog(`Delete recipe ${name}?`);
  if (!confirmed) return;
  await api(`/api/recipes/${encodeURIComponent(name)}`, "DELETE");
  hideEditor();
  await refreshRecipes();
  status(`Deleted ${name}`);
}

async function resetRecipe() {
  if (!state.selectedRecipe) return;
  await loadRecipe(state.selectedRecipe);
  status("Recipe reset to saved state");
}

function cancelRecipe() {
  hideEditor();
  refreshRecipes();
}

function selectedRecipes() {
  return Array.from(state.selectedForTransfer.values());
}

async function transfer(action, payload) {
  const result = await api(action, "POST", payload);
  await refreshRecipes();
  status(`Copied: ${result.copied.join(", ") || "(none)"}\nSkipped: ${result.skipped.join(", ") || "(none)"}`);
}

function wireEditorInputs() {
  const editorBody = el("editorBody");
  if (!editorBody) return;
  editorBody.addEventListener("input", () => checkDirty());
  editorBody.addEventListener("change", () => checkDirty());

  const qtyInput = el("recipeQty");
  const pressureInput = el("stepPressure");
  if (qtyInput) qtyInput.addEventListener("input", updatePressurePerContact);
  if (pressureInput) pressureInput.addEventListener("input", updatePressurePerContact);
}

function wireEvents() {
  el("placeholderNewBtn").addEventListener("click", newRecipe);
  el("saveBtn").addEventListener("click", () => saveRecipe().catch(e => status(e.message, true)));
  el("resetBtn").addEventListener("click", () => resetRecipe().catch(e => status(e.message, true)));
  el("cancelBtn").addEventListener("click", cancelRecipe);
  el("deleteBtn").addEventListener("click", () => deleteRecipe().catch(e => status(e.message, true)));
  el("settingsHead").addEventListener("click", (e) => {
    if (e.target.closest("button:not(.panel-toggle)")) return;
    toggleSettings();
  });
  el("settingsToggleBtn").addEventListener("click", (e) => { e.stopPropagation(); toggleSettings(); });
  el("importBtn").addEventListener("click", openImportAccordion);
  el("exportBtn").addEventListener("click", openExportAccordion);
  el("addStepBtn").addEventListener("click", addStep);

  el("exportTypeSelect").addEventListener("change", refreshExportUi);
  el("exportRunBtn").addEventListener("click", () => runExport().catch(e => status(e.message, true)));
  el("exportCancelBtn").addEventListener("click", closeAccordions);
  el("importTypeSelect").addEventListener("change", refreshImportUi);
  el("importRunBtn").addEventListener("click", () => runImport().catch(e => status(e.message, true)));
  el("importCancelBtn").addEventListener("click", closeAccordions);

  const saveSettingsBtn = el("saveSettingsBtn");
  if (saveSettingsBtn) {
    saveSettingsBtn.addEventListener("click", () => saveSettings().catch(e => settingsStatus(e.message, true)));
  }
}

wireEvents();
wireTabs();
wireSettingsEditor();
wireEditorInputs();
wireComboBoxes();
loadConsumables().catch(e => settingsStatus(e.message, true));
refreshRecipes().catch(e => status(e.message, true));
