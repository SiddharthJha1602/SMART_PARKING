"""
ocr/plate_recognition.py
Number plate recognition pipeline:
    1. Load image
    2. Locate the likely number-plate region using OpenCV
       (grayscale -> blur -> edge detection -> contour analysis)
    3. Run EasyOCR on the cropped plate region (falls back to the
       full image if no clear plate contour is found)
    4. Clean / normalize the extracted text
    5. Match against the Vehicle table

This is intentionally dependency-light (OpenCV + EasyOCR only) so it
runs on a standard student laptop with no GPU and no external services.

EasyOCR's Reader is expensive to construct (loads neural net weights),
so we lazily build a single module-level instance and reuse it across
requests.
"""

import os
import re
import cv2
import numpy as np

_reader = None  # lazy-loaded EasyOCR reader singleton


def get_reader():
    """Lazily construct and cache the EasyOCR reader (CPU mode)."""
    global _reader
    if _reader is None:
        import easyocr  # imported lazily so app startup isn't slowed by model loading

        _reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    return _reader


def _locate_plate_contour(image: np.ndarray):
    """
    Attempts to find a rectangular contour likely to be a license plate
    using classic OpenCV edge + contour analysis. Returns a cropped
    BGR image of the plate region, or None if no good candidate is found.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    edged = cv2.Canny(gray, 30, 200)

    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:15]

    plate_contour = None
    for c in contours:
        perimeter = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.018 * perimeter, True)
        if len(approx) == 4:  # rectangle-like shape
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = w / float(h) if h > 0 else 0
            # Typical license plates are wider than tall, roughly 2:1 to 5:1
            if 1.5 <= aspect_ratio <= 6.0 and w > 60 and h > 15:
                plate_contour = (x, y, w, h)
                break

    if plate_contour is None:
        return None

    x, y, w, h = plate_contour
    pad = 4
    y1, y2 = max(y - pad, 0), min(y + h + pad, image.shape[0])
    x1, x2 = max(x - pad, 0), min(x + w + pad, image.shape[1])
    return image[y1:y2, x1:x2]


def normalize_plate_text(raw_text: str) -> str:
    """
    Cleans OCR output into a normalized plate string:
    uppercase, alphanumeric only (Indian plates: e.g. RJ14AB1234).
    """
    text = raw_text.upper()
    text = re.sub(r"[^A-Z0-9]", "", text)
    return text


def recognize_plate(image_path: str) -> dict:
    """
    Runs the full pipeline on an image file and returns:
        {
            "raw_text": str,        # raw OCR text (joined, unprocessed)
            "normalized_text": str, # cleaned, uppercase alphanumeric
            "confidence": float,    # average OCR confidence (0-1)
            "used_crop": bool,      # whether a plate contour was found
        }
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Could not read image. Ensure it is a valid image file.")

    cropped = _locate_plate_contour(image)
    used_crop = cropped is not None
    target = cropped if used_crop else image

    reader = get_reader()
    results = reader.readtext(target)

    if not results and used_crop:
        # Fallback: contour crop might have missed the plate; retry on full image
        results = reader.readtext(image)
        used_crop = False

    if not results:
        return {
            "raw_text": "",
            "normalized_text": "",
            "confidence": 0.0,
            "used_crop": used_crop,
        }

    # Concatenate all detected text fragments, weighted by confidence
    raw_text = " ".join(r[1] for r in results)
    avg_confidence = sum(r[2] for r in results) / len(results)
    normalized = normalize_plate_text(raw_text)

    return {
        "raw_text": raw_text,
        "normalized_text": normalized,
        "confidence": round(float(avg_confidence), 3),
        "used_crop": used_crop,
    }


def match_vehicle_by_plate(normalized_text: str):
    """
    Attempts to find a Vehicle whose stored number matches the OCR
    output. Uses exact match first, then a fuzzy fallback (substring /
    near match) since OCR often confuses similar characters (0/O, 1/I).
    """
    from models import Vehicle  # local import to avoid circulars at module load

    if not normalized_text:
        return None

    exact = Vehicle.query.filter_by(vehicle_number=normalized_text).first()
    if exact:
        return exact

    # Fuzzy fallback: compare against all vehicle numbers, normalized
    all_vehicles = Vehicle.query.all()
    best_match = None
    best_score = 0
    for v in all_vehicles:
        candidate = normalize_plate_text(v.vehicle_number)
        score = _similarity(normalized_text, candidate)
        if score > best_score:
            best_score = score
            best_match = v

    # Require a reasonably high similarity to avoid false positives
    if best_match and best_score >= 0.75:
        return best_match
    return None


def _similarity(a: str, b: str) -> float:
    """Simple normalized similarity based on longest common subsequence length."""
    if not a or not b:
        return 0.0
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    lcs = dp[m][n]
    return (2 * lcs) / (m + n)
