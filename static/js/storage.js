document.addEventListener("DOMContentLoaded", () => {

  // ── Image preview for any file input with paired preview img ──
  function setupPreview(inputId, previewId) {
    const inp = document.getElementById(inputId);
    const prev = document.getElementById(previewId);
    if (!inp || !prev) return;

    inp.addEventListener("change", () => {
      const file = inp.files[0];
      if (!file) { prev.style.display = "none"; return; }
      if (!file.type.startsWith("image/")) { prev.style.display = "none"; return; }
      const reader = new FileReader();
      reader.onload = (e) => {
        prev.src = e.target.result;
        prev.style.display = "block";
      };
      reader.readAsDataURL(file);
    });
  }

  setupPreview("reportFile", "reportPreview");
  setupPreview("medFile",    "medPreview");

  // ── Drag & Drop highlight ──────────────────────────────────
  document.querySelectorAll(".file-drop-zone").forEach(zone => {
    zone.addEventListener("dragover", e => { e.preventDefault(); zone.classList.add("dragover"); });
    zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));
    zone.addEventListener("drop", e => {
      e.preventDefault(); zone.classList.remove("dragover");
      const input = zone.querySelector("input[type=file]");
      const preview = zone.querySelector(".img-preview");
      if (input && e.dataTransfer.files.length) {
        input.files = e.dataTransfer.files;
        if (preview && e.dataTransfer.files[0].type.startsWith("image/")) {
          const reader = new FileReader();
          reader.onload = ev => { preview.src = ev.target.result; preview.style.display = "block"; };
          reader.readAsDataURL(e.dataTransfer.files[0]);
        }
        input.dispatchEvent(new Event("change"));
      }
    });
  });

  // ── Delete confirmation ────────────────────────────────────
  document.querySelectorAll(".del-form").forEach(form => {
    form.addEventListener("submit", e => {
      if (!confirm("Permanently delete this item?")) e.preventDefault();
    });
  });

});