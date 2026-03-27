import os
from datetime import datetime
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, current_app, send_from_directory)
from flask_login import login_required, current_user
from database import db

storage_bp = Blueprint("storage", __name__, url_prefix="/storage")


class StorageItem(db.Model):
    __tablename__ = "storage_item"
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, nullable=False, index=True)
    category    = db.Column(db.String(30), nullable=False)   # prescription / medicine
    filename    = db.Column(db.String(255), nullable=False)
    title       = db.Column(db.String(255), default="")
    notes       = db.Column(db.Text, default="")
    date_taken  = db.Column(db.String(30), default="")       # yyyy-mm-dd
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


def _folder(category: str) -> str:
    if category == "prescription":
        return current_app.config["UPLOAD_PRESCRIPTIONS"]
    if category == "medicine":
        return current_app.config["UPLOAD_MEDICINES"]
    raise ValueError("Invalid category")


# ── Hub redirect ──────────────────────────────────────────────────────────────
@storage_bp.route("/")
@login_required
def page():
    return redirect(url_for("storage.reports"))


# ── Report Storage ─────────────────────────────────────────────────────────
@storage_bp.route("/reports", methods=["GET"])
@login_required
def reports():
    items = (StorageItem.query
             .filter_by(user_id=current_user.id, category="prescription")
             .order_by(StorageItem.date_taken.asc(), StorageItem.uploaded_at.asc())
             .all())
    return render_template("storage_reports.html", items=items)


# ── Medicine Storage ───────────────────────────────────────────────────────
@storage_bp.route("/medicines", methods=["GET"])
@login_required
def medicines():
    items = (StorageItem.query
             .filter_by(user_id=current_user.id, category="medicine")
             .order_by(StorageItem.date_taken.asc(), StorageItem.uploaded_at.asc())
             .all())
    return render_template("storage_medicines.html", items=items)


# ── Upload ─────────────────────────────────────────────────────────────────
@storage_bp.route("/upload/<category>", methods=["POST"])
@login_required
def upload(category):
    category = category.strip().lower()
    f         = request.files.get("file")
    title     = request.form.get("title", "").strip()
    notes     = request.form.get("notes", "").strip()
    date_taken = request.form.get("date_taken", "").strip()

    if category not in ["prescription", "medicine"]:
        flash("Invalid category.", "danger")
        return redirect(url_for("storage.reports"))

    if not f or f.filename == "":
        flash("No file selected.", "danger")
        return _redirect_for(category)

    # Validate extension
    allowed = {"png", "jpg", "jpeg", "gif", "webp", "pdf", "bmp", "tiff"}
    ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
    if ext not in allowed:
        flash(f"File type .{ext} is not allowed. Use: {', '.join(sorted(allowed))}", "danger")
        return _redirect_for(category)

    folder = _folder(category)
    os.makedirs(folder, exist_ok=True)

    safe_name = f"{current_user.id}_{category}_{int(datetime.utcnow().timestamp())}_{f.filename}"
    f.save(os.path.join(folder, safe_name))

    item = StorageItem(
        user_id=current_user.id,
        category=category,
        filename=safe_name,
        title=title,
        notes=notes,
        date_taken=date_taken
    )
    db.session.add(item)
    db.session.commit()

    flash(f"Uploaded successfully! ✅", "success")
    return _redirect_for(category)


# ── Edit ───────────────────────────────────────────────────────────────────
@storage_bp.route("/edit/<int:item_id>", methods=["POST"])
@login_required
def edit(item_id):
    item = StorageItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for("storage.reports"))

    item.title      = request.form.get("title", "").strip()
    item.notes      = request.form.get("notes", "").strip()
    item.date_taken = request.form.get("date_taken", "").strip()
    db.session.commit()

    flash("Record updated. ✅", "success")
    return _redirect_for(item.category)


# ── Delete ─────────────────────────────────────────────────────────────────
@storage_bp.route("/delete/<int:item_id>", methods=["POST"])
@login_required
def delete(item_id):
    item = StorageItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for("storage.reports"))

    cat = item.category
    fp = os.path.join(_folder(cat), item.filename)
    if os.path.exists(fp):
        os.remove(fp)

    db.session.delete(item)
    db.session.commit()
    flash("Deleted successfully.", "success")
    return _redirect_for(cat)


# ── File serve ─────────────────────────────────────────────────────────────
@storage_bp.route("/file/<category>/<path:filename>")
@login_required
def file(category, filename):
    return send_from_directory(_folder(category), filename)


def _redirect_for(cat: str):
    if cat == "prescription":
        return redirect(url_for("storage.reports"))
    return redirect(url_for("storage.medicines"))