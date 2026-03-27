import requests
import urllib.parse

PIN_API = "https://api.postalpincode.in/pincode/{pin}"
HEADERS = {"User-Agent": "Cognisync/1.0 (Flask app)"}

def get_area_from_pincode(pincode: str):
    """
    Uses India Post PIN API (no key).
    Returns:
      (area_label, post_offices_list, district, state)
    or (None, [], None, None) if invalid.
    """
    pincode = (pincode or "").strip()
    if not (pincode.isdigit() and len(pincode) == 6):
        return None, [], None, None

    url = PIN_API.format(pin=pincode)
    r = requests.get(url, headers=HEADERS, timeout=15)
    data = r.json()

    if not data or not isinstance(data, list):
        return None, [], None, None

    item = data[0]
    if item.get("Status") != "Success":
        return None, [], None, None

    po = item.get("PostOffice") or []
    if not po:
        return None, [], None, None

    # Take district/state from first PostOffice
    district = po[0].get("District")
    state = po[0].get("State")

    # Build label and list
    post_offices = []
    for x in po:
        name = x.get("Name")
        division = x.get("Division")
        region = x.get("Region")
        if name:
            post_offices.append({
                "name": name,
                "division": division or "",
                "region": region or "",
            })

    area_label = f"{pincode} • {district}, {state}"
    return area_label, post_offices, district, state


def build_maps_search_url(query: str):
    """
    No API key Google Maps search URL.
    """
    q = urllib.parse.quote_plus(query)
    return f"https://www.google.com/maps/search/{q}"


def mental_health_maps_links(district: str, state: str):
    """
    Returns a few map links for the same area.
    """
    base = f"{district}, {state}, India"
    return [
        {"label": "Psychiatrist near me", "url": build_maps_search_url(f"psychiatrist near {base}")},
        {"label": "Mental health hospital", "url": build_maps_search_url(f"mental health hospital near {base}")},
        {"label": "Psychologist / counselling", "url": build_maps_search_url(f"psychologist counselling near {base}")},
        {"label": "Government hospital", "url": build_maps_search_url(f"government hospital near {base}")},
    ]