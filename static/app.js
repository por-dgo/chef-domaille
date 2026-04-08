const state = {
  recipes: [],
  selectedRecipe: null,
  bundle: null,
  currentStepIndex: 0,
  selectedForTransfer: new Set(),
  consumables: { Film: [], Pad: [], Lubricant: [] },
};

function el(id) { return document.getElementById(id); }

function status(msg, isError = false) {
  const box = el("statusBox");
  box.textContent = msg;
  box.style.color = isError ? "#ff9e9e" : "#c7ffd4";
}

function settingsStatus(msg, isError = false) {
  const box = el("settingsStatusBox");
  if (!box) return;
  box.textContent = msg;
  box.style.color = isError ? "#ff9e9e" : "#c7ffd4";
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
    populateSelectDropdowns();
    loadSettingsEditor();
  } catch (e) {
    console.error("Failed to load consumables:", e);
  }
}

function populateSelectDropdowns() {
  for (const [category, options] of Object.entries(state.consumables)) {
    const selectId = `step${category}`;
    const select = el(selectId);
    if (!select) continue;
    select.innerHTML = "";
    for (const opt of options) {
      const option = document.createElement("option");
      option.value = opt;
      option.textContent = opt;
      select.appendChild(option);
    }
  }
}

function setSelectValue(id, value) {
  const select = el(id);
  if (!select) return;
  const safeValue = value || "";
  const exists = Array.from(select.options).some((option) => option.value === safeValue);
  if (!exists && safeValue) {
    const dynamicOption = document.createElement("option");
    dynamicOption.value = safeValue;
    dynamicOption.textContent = `${safeValue} (custom)`;
    select.appendChild(dynamicOption);
  }
  select.value = safeValue;
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

function renderOptionChips(kind) {
  const idPrefix = kind.toLowerCase();
  const container = el(`${idPrefix}OptionList`);
  if (!container) return;
  container.innerHTML = "";
  const values = state.consumables[kind] || [];
  for (const value of values) {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = value;

    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "chip-remove";
    removeBtn.textContent = "x";
    removeBtn.setAttribute("aria-label", `Remove ${value}`);
    removeBtn.addEventListener("click", () => {
      state.consumables[kind] = values.filter((item) => item !== value);
      renderOptionChips(kind);
      populateSelectDropdowns();
    });

    chip.appendChild(removeBtn);
    container.appendChild(chip);
  }
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
    populateSelectDropdowns();
    loadSettingsEditor();
    settingsStatus("Settings saved!");
  } catch (e) {
    settingsStatus(e.message, true);
  }
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
  step.rRecipeStepFCI = el("stepFCI").value;
  step.strRecipeStepDescription1 = el("stepNote1").value;
  step.strRecipeStepDescription2 = el("stepNote2").value;
  step.rRecipeStepLowerSpeedLimit = el("stepLowerSpeed").value;
  step.rRecipeStepUpperSpeedLimit = el("stepUpperSpeed").value;
  step.rRecipeStepLowerPressureLimit = el("stepLowerPressure").value;
  step.rRecipeStepUpperPressureLimit = el("stepUpperPressure").value;
  step.rRecipeStepFixtureWeight = el("stepFixtureWeight").value;
  step.intRecipeStepOpCode = el("stepOpCode").value;
}

function renderCurrentStep() {
  if (!state.bundle) return;
  const step = state.bundle.steps[state.currentStepIndex];
  el("stepLabel").textContent = `Step ${state.currentStepIndex + 1}`;
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
  el("stepFCI").value = step.rRecipeStepFCI || "0";
  el("stepNote1").value = step.strRecipeStepDescription1 || "";
  el("stepNote2").value = step.strRecipeStepDescription2 || "";
  el("stepLowerSpeed").value = step.rRecipeStepLowerSpeedLimit || "";
  el("stepUpperSpeed").value = step.rRecipeStepUpperSpeedLimit || "";
  el("stepLowerPressure").value = step.rRecipeStepLowerPressureLimit || "";
  el("stepUpperPressure").value = step.rRecipeStepUpperPressureLimit || "";
  el("stepFixtureWeight").value = step.rRecipeStepFixtureWeight || "";
  el("stepOpCode").value = step.intRecipeStepOpCode || "";
}

function updateBundleFromHeader() {
  if (!state.bundle) return;
  state.bundle.recipe_name = el("recipeName").value.trim();
  state.bundle.recipe_data.strRecipeDescription = el("recipeDescription").value;
  state.bundle.recipe_data.intRecipeQty = el("recipeQty").value;
  state.bundle.recipe_data.intRecipeReworkStep = el("recipeRework").value;

  const requestedSteps = parseInt(el("recipeSteps").value || "1", 10);
  while (state.bundle.steps.length < requestedSteps) state.bundle.steps.push(defaultStep());
  while (state.bundle.steps.length > requestedSteps) state.bundle.steps.pop();
  state.bundle.recipe_data.intRecipeNoOfSteps = String(state.bundle.steps.length);
  if (state.currentStepIndex > state.bundle.steps.length - 1) {
    state.currentStepIndex = state.bundle.steps.length - 1;
  }
}

function renderBundleHeader() {
  if (!state.bundle) return;
  el("recipeName").value = state.bundle.recipe_name;
  el("recipeDescription").value = state.bundle.recipe_data.strRecipeDescription || "";
  el("recipeSteps").value = String(state.bundle.steps.length);
  el("recipeQty").value = state.bundle.recipe_data.intRecipeQty || "";
  el("recipeRework").value = state.bundle.recipe_data.intRecipeReworkStep || "1";
}

async function refreshRecipes() {
  const data = await api("/api/recipes");
  state.recipes = data.recipes;
  const list = el("recipeList");
  list.innerHTML = "";
  for (const name of state.recipes) {
    const li = document.createElement("li");
    if (name === state.selectedRecipe) li.classList.add("active");

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = state.selectedForTransfer.has(name);
    checkbox.addEventListener("change", () => {
      if (checkbox.checked) state.selectedForTransfer.add(name);
      else state.selectedForTransfer.delete(name);
    });

    const button = document.createElement("button");
    button.textContent = name;
    button.addEventListener("click", () => loadRecipe(name));

    li.appendChild(checkbox);
    li.appendChild(button);
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
  renderBundleHeader();
  renderCurrentStep();
  refreshRecipes();
  status(`Loaded ${name}`);
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
  renderBundleHeader();
  renderCurrentStep();
  status("New recipe draft created");
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
  await api(`/api/recipes/${encodeURIComponent(name)}`, "PUT", {
    recipe_data: state.bundle.recipe_data,
    steps: state.bundle.steps,
  });
  state.selectedRecipe = name;
  await refreshRecipes();
  status(`Saved ${name}`);
}

async function deleteRecipe() {
  const name = el("recipeName").value.trim();
  if (!name) return;
  if (!confirm(`Delete recipe ${name}?`)) return;
  await api(`/api/recipes/${encodeURIComponent(name)}`, "DELETE");
  state.bundle = null;
  state.selectedRecipe = null;
  await refreshRecipes();
  status(`Deleted ${name}`);
}

function selectedRecipes() {
  return Array.from(state.selectedForTransfer.values());
}

async function transfer(action, payload) {
  const result = await api(action, "POST", payload);
  await refreshRecipes();
  status(`Copied: ${result.copied.join(", ") || "(none)"}\nSkipped: ${result.skipped.join(", ") || "(none)"}`);
}

function wireEvents() {
  el("newRecipeBtn").addEventListener("click", newRecipe);
  el("refreshBtn").addEventListener("click", refreshRecipes);
  el("saveBtn").addEventListener("click", () => saveRecipe().catch(e => status(e.message, true)));
  el("deleteBtn").addEventListener("click", () => deleteRecipe().catch(e => status(e.message, true)));

  el("stepPrevBtn").addEventListener("click", () => {
    if (!state.bundle) return;
    bindCurrentStepInputs();
    state.currentStepIndex = Math.max(0, state.currentStepIndex - 1);
    renderCurrentStep();
  });

  el("stepNextBtn").addEventListener("click", () => {
    if (!state.bundle) return;
    bindCurrentStepInputs();
    state.currentStepIndex = Math.min(state.bundle.steps.length - 1, state.currentStepIndex + 1);
    renderCurrentStep();
  });

  el("importThumbBtn").addEventListener("click", () => {
    transfer("/api/transfer/import/thumb", {
      source_path: el("thumbImportPath").value,
      selected_recipes: selectedRecipes(),
      overwrite: true,
    }).catch(e => status(e.message, true));
  });

  el("exportThumbBtn").addEventListener("click", () => {
    transfer("/api/transfer/export/thumb", {
      destination_path: el("thumbExportPath").value,
      selected_recipes: selectedRecipes(),
    }).catch(e => status(e.message, true));
  });

  el("importZipBtn").addEventListener("click", () => {
    transfer("/api/transfer/import/zip", {
      zip_path: el("zipImportPath").value,
      selected_recipes: selectedRecipes(),
      overwrite: true,
    }).catch(e => status(e.message, true));
  });

  el("exportZipBtn").addEventListener("click", () => {
    transfer("/api/transfer/export/zip", {
      zip_path: el("zipExportPath").value,
      selected_recipes: selectedRecipes(),
    }).catch(e => status(e.message, true));
  });

  const saveSettingsBtn = el("saveSettingsBtn");
  if (saveSettingsBtn) {
    saveSettingsBtn.addEventListener("click", () => saveSettings().catch(e => settingsStatus(e.message, true)));
  }
}

wireEvents();
wireTabs();
wireSettingsEditor();
loadConsumables().catch(e => settingsStatus(e.message, true));
refreshRecipes().catch(e => status(e.message, true));
newRecipe();
