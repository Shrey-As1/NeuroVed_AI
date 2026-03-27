import cv2
import pytesseract
import platform
import os

if platform.system() == "Windows":
    _tesseract_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.join(os.getenv('LOCALAPPDATA', ''), 'Programs', 'Tesseract-OCR', 'tesseract.exe')
    ]
    for _p in _tesseract_paths:
        if os.path.exists(_p):
            pytesseract.pytesseract.tesseract_cmd = _p
            break

img_path = r"c:\Users\KIIT0001\Desktop\NeuroVed_AI 2.0\uploads\analyzer\1_1774582657_WhatsApp Image 2026-03-20 at 3.28.57 PM (1).jpeg"
img = cv2.imread(img_path)

with open("test_ocr_results.txt", "w", encoding="utf-8") as f:
    def ocr_test(name, processed, psm=6):
        try:
            text = pytesseract.image_to_string(processed, config=f'--oem 3 --psm {psm}')
            f.write(f"--- {name} (PSM {psm}) length {len(text)} ---\n")
            f.write(text.replace('\n', ' ')[:500] + "\n\n")
        except Exception as e:
            f.write(f"--- {name} ERROR ---\n{str(e)}\n\n")

    # 1. Base grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ocr_test("Base Grayscale", gray, 6)

    # 2. Otsu
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    ocr_test("Otsu", otsu, 6)
    
    # 3. Adaptive (small block)
    adapt_small = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 10)
    ocr_test("Adapt 21", adapt_small, 6)

    # 4. Adaptive (large block)
    adapt_large = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 81, 15)
    ocr_test("Adapt 81", adapt_large, 6)
    
    # 5. CLAHE + Adaptive
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray_clahe = clahe.apply(gray)
    adapt_clahe = cv2.adaptiveThreshold(gray_clahe, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 81, 15)
    ocr_test("CLAHE+Adapt81", adapt_clahe, 6)
    ocr_test("CLAHE+Adapt81_psm3", adapt_clahe, 3)

print("Done writing results.")
