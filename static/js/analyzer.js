document.addEventListener("DOMContentLoaded", () => {

  // ── Image preview on file select ──────────────────────────
  const fileInput = document.getElementById("analyzerFile");
  const preview   = document.getElementById("imgPreview");
  const dropLabel = document.getElementById("dropLabel");
  const submitBtn = document.getElementById("submitBtn");
  const form      = document.getElementById("analyzerForm");

  if (fileInput && preview) {
    fileInput.addEventListener("change", () => {
      const file = fileInput.files[0];
      if (!file) { preview.style.display = "none"; return; }

      const reader = new FileReader();
      reader.onload = (e) => {
        preview.src = e.target.result;
        preview.style.display = "block";
        if (dropLabel) dropLabel.style.display = "none";
      };
      reader.readAsDataURL(file);
    });
  }

  // ── Drag & Drop ───────────────────────────────────────────
  const dropZone = document.getElementById("dropZone");
  if (dropZone) {
    dropZone.addEventListener("dragover", e => { e.preventDefault(); dropZone.classList.add("dragover"); });
    dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
    dropZone.addEventListener("drop", e => {
      e.preventDefault(); dropZone.classList.remove("dragover");
      if (fileInput && e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        fileInput.dispatchEvent(new Event("change"));
      }
    });
  }

  // ── Loading state on submit ────────────────────────────────
  if (form && submitBtn) {
    form.addEventListener("submit", () => {
      submitBtn.disabled = true;
      submitBtn.textContent = "⏳ Analyzing…";
      submitBtn.style.opacity = "0.7";
    });
  }

});
