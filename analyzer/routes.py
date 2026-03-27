import os
import shutil
from datetime import datetime
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, current_app)
from flask_login import login_required, current_user
from database import db
from storage_bot.routes import StorageItem
from utils.ocr_helper import (
    detect_medicine_name,
    extract_report_keywords,
    build_google_search_url,
    extract_text_from_image
)

analyzer_bp = Blueprint("analyzer", __name__, url_prefix="/analyzer")


def _save_upload(file_obj) -> tuple[str, str]:
    """Save uploaded file to the analyzer folder. Returns (full_path, safe_name)."""
    folder = current_app.config["UPLOAD_ANALYZER"]
    os.makedirs(folder, exist_ok=True)

    safe_name = (
        f"{current_user.id}_{int(datetime.utcnow().timestamp())}_{file_obj.filename}"
    )
    full_path = os.path.join(folder, safe_name)
    file_obj.save(full_path)
    return full_path, safe_name


def _validate_image(f) -> str:
    """Returns an error message if file is invalid, else empty string."""
    if not f or f.filename == "":
        return "No file selected."
    allowed = {"png", "jpg", "jpeg", "gif", "webp", "bmp", "tiff"}
    ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
    if ext not in allowed:
        return f"Only image files are supported ({', '.join(sorted(allowed))})."
    return ""


# ── Hub ───────────────────────────────────────────────────────────────────
@analyzer_bp.route("/")
@login_required
def page():
    return render_template("analyzer.html")


# ── Medicine Analyzer ─────────────────────────────────────────────────────
@analyzer_bp.route("/medicine", methods=["GET", "POST"])
@login_required
def medicine():
    ctx = {
        "ocr_text": "",
        "medicine_name": "",
        "search_url": "",
        "error": "",
        "image_filename": ""
    }

    if request.method == "POST":
        f = request.files.get("image")
        err = _validate_image(f)
        if err:
            ctx["error"] = err
            return render_template("analyzer_medicine.html", **ctx)

        file_path, safe_name = _save_upload(f)
        ctx["image_filename"] = safe_name

        try:
            ocr_text, ocr_err = extract_text_from_image(file_path)
        except Exception as e:
            ocr_text = ""
            ocr_err = str(e)
            
        if ocr_err:
            ctx["error"] = ocr_err
            return render_template("analyzer_medicine.html", **ctx)

        ctx["ocr_text"] = ocr_text
        med_name = detect_medicine_name(ocr_text)
        ctx["medicine_name"] = med_name or "Could not identify"

        if med_name:
            ctx["search_url"] = build_google_search_url(f"{med_name} medicine uses dosage side effects")
            
            med_folder = current_app.config.get("UPLOAD_MEDICINES", "uploads/medicines")
            os.makedirs(med_folder, exist_ok=True)
            new_safe_name = f"{current_user.id}_medicine_{int(datetime.utcnow().timestamp())}_{f.filename}"
            shutil.copy2(file_path, os.path.join(med_folder, new_safe_name))
            
            item = StorageItem(
                user_id=current_user.id,
                category="medicine",
                filename=new_safe_name,
                title="Analyzed Medicine",
                notes=f"Detected Medicine: {med_name}\n\nProcessed by Google Gemini Analyzer.",
                date_taken=datetime.utcnow().strftime("%Y-%m-%d")
            )
            db.session.add(item)
            db.session.commit()
            flash("Analyzed and saved to Medicine Storage vault! ✅", "success")

    return render_template("analyzer_medicine.html", **ctx)


# ── Report Analyzer ───────────────────────────────────────────────────────
@analyzer_bp.route("/report", methods=["GET", "POST"])
@login_required
def report():
    ctx = {
        "ocr_text": "",
        "keyword_links": [],
        "error": "",
        "image_filename": ""
    }

    if request.method == "POST":
        f = request.files.get("image")
        err = _validate_image(f)
        if err:
            ctx["error"] = err
            return render_template("analyzer_report.html", **ctx)

        file_path, safe_name = _save_upload(f)
        ctx["image_filename"] = safe_name

        try:
            ocr_text, ocr_err = extract_text_from_image(file_path)
        except Exception as e:
            ocr_text = ""
            ocr_err = str(e)
            
        if ocr_err:
            ctx["error"] = ocr_err
            return render_template("analyzer_report.html", **ctx)

        ctx["ocr_text"] = ocr_text
        categorized_keywords = extract_report_keywords(ocr_text)
        
        # Flatten for inline text highlighting
        all_keywords = []
        for kws in categorized_keywords.values():
            all_keywords.extend(kws)
            
        annotated_text = ocr_text
        
        # Build categorized tag-clouds for frontend
        categorized_links = {}
        for cat, kws in categorized_keywords.items():
            if not kws: continue
            nice_cat = cat.replace('_', ' ').title()
            links = []
            for kw in kws:
                links.append({"term": kw, "url": build_google_search_url(f"{kw} mental health or medical meaning")})
            categorized_links[nice_cat] = links
            
        ctx["categorized_links"] = categorized_links
        ctx["annotated_text"] = annotated_text
        
        rep_folder = current_app.config.get("UPLOAD_PRESCRIPTIONS", "uploads/prescriptions")
        os.makedirs(rep_folder, exist_ok=True)
        new_safe_name = f"{current_user.id}_prescription_{int(datetime.utcnow().timestamp())}_{f.filename}"
        shutil.copy2(file_path, os.path.join(rep_folder, new_safe_name))
        
        # Save flattened keywords to database Note
        kw_str = ", ".join(all_keywords) if all_keywords else "None"
        item = StorageItem(
            user_id=current_user.id,
            category="prescription",
            filename=new_safe_name,
            title="Analyzed Medical Report",
            notes=f"Extracted Keywords: {kw_str}\n\nProcessed by Google Gemini Analyzer.",
            date_taken=datetime.utcnow().strftime("%Y-%m-%d")
        )
        db.session.add(item)
        db.session.commit()
        flash("Analyzed and saved to Report Storage vault! ✅", "success")

    return render_template("analyzer_report.html", **ctx)
