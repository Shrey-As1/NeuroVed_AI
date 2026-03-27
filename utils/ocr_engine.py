import os
import cv2
import re
import numpy as np
import pytesseract

try:
    from pdf2image import convert_from_path
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False

def clean_ocr_text(text: str) -> str:
    """Normalize extracted text by cleaning up noise, spaces, and line breaks."""
    # Remove multiple spaces/tabs
    text = re.sub(r'[ \t]+', ' ', text)
    # Remove multiple line breaks
    text = re.sub(r'\n\s*\n', '\n', text)
    # Remove bizarre non-ascii noise characters sometimes produced by Tesseract
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    return text.strip()

def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    OpenCV Preprocessing Pipeline:
    1. Resize image (upscale for better OCR accuracy)
    2. Convert to grayscale
    3. Median blur (noise removal)
    4. Adaptive thresholding
    """
    # 1. Resize (scale 1.5x)
    width = int(image.shape[1] * 1.5)
    height = int(image.shape[0] * 1.5)
    dim = (width, height)
    resized = cv2.resize(image, dim, interpolation=cv2.INTER_CUBIC)

    # 2. Grayscale
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    # 3. Noise removal via Median Blur
    blurred = cv2.medianBlur(gray, 3)

    # 4. Adaptive Thresholding (Binary)
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    return thresh

def process_pdf(pdf_path: str) -> str:
    """Convert PDF to images and run OCR on each page."""
    if not HAS_PDF2IMAGE:
        return "PDF processing requires 'pdf2image' and Poppler installed on the system."
    try:
        pages = convert_from_path(pdf_path, 300)
        full_text = []
        for page in pages:
            # Convert PIL image to OpenCV format
            open_cv_image = np.array(page) 
            open_cv_image = open_cv_image[:, :, ::-1].copy() # RGB to BGR
            
            processed = preprocess_image(open_cv_image)
            text = pytesseract.image_to_string(processed, config=r'--oem 3 --psm 6')
            full_text.append(text)
        return clean_ocr_text("\n".join(full_text))
    except Exception as e:
        return f"Error processing PDF: {str(e)}"

def extract_text(file_path: str) -> str:
    """
    Main entry point for OCR extraction. Handles Images and PDFs.
    Returns cleaned text.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError("File not found.")
        
    ext = file_path.lower().rsplit('.', 1)[-1]
    
    if ext == 'pdf':
        return process_pdf(file_path)
        
    # Read standard image
    img = cv2.imread(file_path)
    if img is None:
        raise ValueError("Could not read image file.")
        
    processed = preprocess_image(img)
    text = pytesseract.image_to_string(processed, config=r'--oem 3 --psm 6')
    return clean_ocr_text(text)
