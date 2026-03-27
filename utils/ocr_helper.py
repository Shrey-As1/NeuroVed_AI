"""OCR helper for the Analyzer module.
Uses Gemini 1.5 Flash Vision API to extract text from images instead of Tesseract.
"""
import os
import re
import urllib.parse
from PIL import Image
from google import genai

# ── Common drug/medicine name patterns ────────────────────────────────────────
_MEDICINE_SUFFIXES = re.compile(
    r"\b\w*(?:mycin|cillin|mide|pril|sartan|statin|olol|oxacin|azole|"
    r"cycline|fenac|phen|dryl|pine|zepam|xine|ipine|formin|bital|"
    r"done|olone|amine|tide|zole|nide|oxone|pam|lam|thiazide|"
    r"caine|cort|pred|sone|rone|diol|sterol|parin|mab|nib|ximab|zumab)\b",
    re.IGNORECASE
)

_COMMON_MEDICINES = {
    "paracetamol", "ibuprofen", "aspirin", "amoxicillin", "azithromycin",
    "ciprofloxacin", "metformin", "atorvastatin", "omeprazole", "pantoprazole",
    "cetirizine", "loratadine", "montelukast", "salbutamol", "levothyroxine",
    "amlodipine", "atenolol", "losartan", "metoprolol", "digoxin",
    "warfarin", "clopidogrel", "hydrochlorothiazide", "furosemide", "spironolactone",
    "prednisone", "prednisolone", "dexamethasone", "hydrocortisone",
    "amitriptyline", "sertraline", "fluoxetine", "escitalopram", "paroxetine",
    "alprazolam", "clonazepam", "diazepam", "lorazepam", "zolpidem",
    "tramadol", "codeine", "morphine", "fentanyl", "gabapentin",
    "pregabalin", "carbamazepine", "valproate", "lamotrigine", "levetiracetam",
    "vitamin", "calcium", "iron", "zinc", "folic", "b12", "d3",
    "dolo", "crocin", "combiflam", "allegra", "zyrtec", "benadryl",
    "pantop", "omez", "gelusil", "digene", "cremaffin",
    "metrogyl", "tiniba", "norflox", "cifran", "mox",
}

def extract_text_from_image(image_path: str) -> tuple[str, str]:
    """
    Returns (ocr_text, error_message).
    Uses Gemini Vision API to extract text.
    ocr_text is empty string on failure.
    """
    if not os.path.exists(image_path):
        return "", "Image file not found."

    from dotenv import load_dotenv
    load_dotenv(override=True)

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return "", "GEMINI_API_KEY is not set. Please set it to use the Analyzer."

    try:
        client = genai.Client(api_key=api_key)
        
        img = Image.open(image_path)
        prompt = "Extract all text from this image exactly as it appears. Do not add any extra commentary or formatting. If there is a medicine name or medical keywords, make sure they are spelled correctly."
        
        models_to_try = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
        response = None
        last_error = None
        
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[prompt, img]
                )
                break
            except Exception as e:
                last_error = e
                if "429" in str(e) or "quota" in str(e).lower():
                    continue
                else:
                    raise e
                    
        if response is None:
            raise last_error or Exception("Failed to get a response from any model.")
        try:
            text = response.text.strip()
        except ValueError:
            return "", "Image was blocked by safety filters or no readable text was returned by the model."
        
        if not text:
            return "", "No text could be extracted from the image. Try a clearer photo."
        return text, ""
    except Exception as e:
        return "", f"Vision API error: {str(e)}"

def detect_medicine_name(ocr_text: str) -> str:
    """
    Heuristic: look for known medicine names or suffix patterns in OCR text.
    Returns the best candidate or empty string.
    """
    if not ocr_text:
        return ""

    words = re.findall(r"[A-Za-z]{4,}", ocr_text)
    candidates = []

    for word in words:
        wl = word.lower()
        if wl in _COMMON_MEDICINES:
            candidates.append((word, 2))  # priority 2 = known medicine
        elif _MEDICINE_SUFFIXES.search(word):
            candidates.append((word, 1))  # priority 1 = suffix match

    if not candidates:
        for word in words:
            if len(word) >= 5:
                return word.capitalize()
        return ""

    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0].capitalize()

def extract_report_keywords(ocr_text: str) -> dict:
    """
    Extract meaningful medical keywords from OCR report text using Gemini JSON.
    Returns a dict with categories: 'diseases', 'symptoms', 'medicines', 'medical_terms'.
    """
    default_dict = {"diseases": [], "symptoms": [], "medicines": [], "medical_terms": []}
    if not ocr_text:
        return default_dict

    from dotenv import load_dotenv
    load_dotenv(override=True)

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return default_dict

    import json
    try:
        client = genai.Client(api_key=api_key)
        prompt = (
            "Extract distinct medical entities from the following text into exactly four categories: "
            "'diseases', 'symptoms', 'medicines', and 'medical_terms'. "
            "Return EXACTLY a valid JSON object matching those four keys mapping to arrays of strings, "
            "and absolutely nothing else (no markdown blocks, no extra text). "
            "Ensure you ONLY include terms that are literally present in the text.\n\n"
            f"Text:\n{ocr_text}"
        )
        
        models_to_try = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
        response = None
        last_error = None
        
        for model_name in models_to_try:
            try:
                # Ask Gemini to natively return JSON
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=genai.types.GenerateContentConfig(
                        response_mime_type="application/json",
                    )
                )
                break
            except Exception as e:
                last_error = e
                if "429" in str(e) or "quota" in str(e).lower():
                    continue
                else:
                    raise e
                    
        if response is None:
            raise last_error or Exception("Failed to get a response from any model.")

        text = response.text.strip()
        data = json.loads(text)
        
        # Verify they exist in the original text to prevent hallucination
        verified_data = {"diseases": [], "symptoms": [], "medicines": [], "medical_terms": []}
        lower_ocr = ocr_text.lower()
        seen = set()
        
        for category in verified_data.keys():
            if category in data and isinstance(data[category], list):
                for term in data[category]:
                    term_str = str(term).strip()
                    low = term_str.lower()
                    if len(term_str) >= 3 and low in lower_ocr and low not in seen:
                        verified_data[category].append(term_str)
                        seen.add(low)
                        
        return verified_data
    except Exception as e:
        print(f"Keyword Extraction Error: {e}")
        return default_dict

def build_google_search_url(query: str) -> str:
    q = urllib.parse.quote_plus(query)
    return f"https://www.google.com/search?q={q}"
