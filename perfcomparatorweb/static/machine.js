"use strict";

const machineInventory = document.getElementById("machine-inventory");

if (machineInventory) {
  const query = new URLSearchParams(window.location.search);
  const options = new URLSearchParams();
  for (const key of ["saved", "edit_error"]) {
    if (query.get(key) === "1") options.set(key, "1");
  }

  const queryString = options.toString();
  const suffix = queryString ? `?${queryString}` : "";
  fetch(`/machine/inventory${suffix}`, { headers: { Accept: "text/html" } })
    .then((response) => response.text())
    .then((html) => {
      machineInventory.innerHTML = html;
      machineInventory.setAttribute("aria-busy", "false");
    })
    .catch(() => {
      machineInventory.innerHTML =
        '<section aria-labelledby="machine-error-title"><h2 id="machine-error-title">Chargement impossible</h2><p role="alert">La fiche Machine n’a pas pu être chargée. Vérifiez que PCE fonctionne, puis <a href="/">réessayez</a>.</p></section>';
      machineInventory.setAttribute("aria-busy", "false");
    });
}

document.addEventListener("submit", (event) => {
  const form = event.target;
  if (!(form instanceof HTMLFormElement) || !form.matches(".metadata-form")) return;

  const waitStatus = form.querySelector(".machine-save-wait");
  const submitButton = form.querySelector('button[type="submit"]');
  if (waitStatus) waitStatus.hidden = false;
  form.setAttribute("aria-busy", "true");
  if (submitButton) {
    submitButton.disabled = true;
    submitButton.textContent = "Enregistrement en cours…";
  }
});
