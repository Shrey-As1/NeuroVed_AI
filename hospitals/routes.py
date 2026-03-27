from flask import Blueprint, render_template, request
from flask_login import login_required

from utils.hospital_locator import get_area_from_pincode, mental_health_maps_links

hosp_bp = Blueprint("hospitals", __name__, url_prefix="/hospitals")


@hosp_bp.route("/", methods=["GET", "POST"])
@login_required
def page():
    error = ""
    pincode = ""
    area_label = ""
    post_offices = []
    map_links = []

    if request.method == "POST":
        pincode = (request.form.get("pincode") or "").strip()

        area_label, post_offices, district, state = get_area_from_pincode(pincode)
        if not area_label:
            error = "Please enter a valid 6-digit Indian pincode."
        else:
            map_links = mental_health_maps_links(district, state)

    return render_template(
        "hospitals.html",
        error=error,
        pincode=pincode,
        area_label=area_label,
        post_offices=post_offices,
        map_links=map_links
    )