"""
Category Suggester – Phase C + E: AI category suggestion for receipt scans.

Priority order:
  1. Learned mappings  – exact merchant the user previously confirmed (Phase E)
  2. Keyword matching  – built-in keyword dictionary (Phase C)

No external ML model required.
"""
from __future__ import annotations

import re
from typing import Optional


# ---------------------------------------------------------------------------
# Keyword map:  category_type  →  keywords that imply that type
# Keywords are matched against: merchant name + first 300 chars of OCR text
# ---------------------------------------------------------------------------
_KEYWORD_MAP: dict[str, list[str]] = {
    "food": [
        "restaurant", "cafe", "coffee", "pizza", "burger", "sushi", "grill",
        "bistro", "diner", "bakery", "donut", "bagel", "sandwich", "noodle",
        "ramen", "kebab", "shawarma", "taco", "burrito", "steakhouse",
        "brasserie", "tavern", "pub", "bar", "lounge", "eatery", "kitchen",
        "starbucks", "dunkin", "mcdonalds", "mcdonald", "kfc", "burger king",
        "subway", "chipotle", "wendys", "dominos", "papa john", "little caesar",
        "panera", "five guys", "shake shack", "popeyes", "chick-fil-a",
        "tim hortons", "costa", "pret", "greggs",
    ],
    "groceries": [
        "supermarket", "grocery", "groceries", "market", "hypermarket",
        "whole foods", "trader joe", "safeway", "kroger", "costco", "aldi",
        "lidl", "migros", "carrefour", "metro", "rewe", "edeka", "tesco",
        "asda", "morrisons", "sainsbury", "waitrose", "marks & spencer",
        "bim", "a101", "sok", "migros", "hakmar",
    ],
    "transport": [
        "uber", "lyft", "taxi", "cab", "fuel", "petrol", "gasoline", "diesel",
        "shell", "bp", "exxon", "chevron", "mobil", "opet", "total energies",
        "parking", "metro", "subway transit", "train", "bus ticket",
        "airline", "airways", "flight", "airport", "toll", "ferry",
    ],
    "shopping": [
        "amazon", "ebay", "etsy", "walmart", "target", "best buy",
        "zara", "h&m", "mango", "uniqlo", "gap", "old navy", "forever 21",
        "primark", "asos", "shein", "zalando", "about you",
        "clothing", "apparel", "fashion", "boutique", "outlet",
        "electronics", "hardware", "ikea", "home depot", "lowes",
    ],
    "health": [
        "pharmacy", "drugstore", "cvs", "walgreens", "rite aid", "boots",
        "hospital", "clinic", "doctor", "physician", "medical center",
        "dental", "dentist", "optician", "vision", "eyecare",
        "eczane", "hastane", "saglik",
    ],
    "entertainment": [
        "cinema", "movie", "theater", "theatre", "concert", "museum",
        "netflix", "spotify", "apple music", "disney", "hulu",
        "game", "bowling", "laser", "escape room", "theme park",
        "zoo", "aquarium", "gallery", "exhibit",
    ],
    "utilities": [
        "electric", "electricity", "water bill", "gas bill", "internet",
        "broadband", "phone bill", "mobile bill", "utility", "utilities",
        "telco", "telecom", "isyeri", "fatura",
    ],
    "accommodation": [
        "hotel", "motel", "airbnb", "hostel", "inn", "resort", "lodge",
        "b&b", "bed and breakfast", "suites",
    ],
    "education": [
        "school", "university", "college", "tuition", "course", "udemy",
        "coursera", "book", "textbook", "stationery", "office supply",
    ],
    "personal care": [
        "salon", "barber", "haircut", "spa", "nail", "beauty",
        "cosmetic", "sephora", "ulta", "bath", "body works",
    ],
}

# ---------------------------------------------------------------------------
# Synonym map:  category_type  →  words commonly found in user category names
# Used to match the inferred type against the user's own category names
# ---------------------------------------------------------------------------
_SYNONYMS: dict[str, list[str]] = {
    "food":          ["food", "dining", "restaurant", "eat", "drink", "cafe", "meal", "lunch", "dinner", "breakfast"],
    "groceries":     ["groceries", "grocery", "supermarket", "market", "food shop"],
    "transport":     ["transport", "travel", "fuel", "gas", "petrol", "car", "commute", "transit"],
    "shopping":      ["shopping", "clothes", "clothing", "apparel", "retail"],
    "health":        ["health", "medical", "pharmacy", "doctor", "hospital", "dental"],
    "entertainment": ["entertainment", "fun", "leisure", "hobby", "movies", "music"],
    "utilities":     ["utilities", "bills", "electric", "water", "internet", "phone"],
    "accommodation": ["hotel", "accommodation", "lodging", "travel"],
    "education":     ["education", "school", "learning", "books", "course"],
    "personal care": ["personal", "care", "beauty", "grooming", "salon"],
}


def _normalise(text: str) -> str:
    """Lowercase, remove punctuation, collapse whitespace."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalise_merchant_key(merchant: str) -> str:
    """Produce a stable lookup key from a raw merchant name.
    Keeps first 3 words (covers 'Defacto Perakende Ticare' → 'defacto perakende ticare')
    so minor OCR variation in the tail doesn't prevent matching.
    """
    key = _normalise(merchant)
    words = key.split()
    return " ".join(words[:3]) if len(words) > 3 else key


def _check_learned_mapping(
    merchant: Optional[str],
    db,
    user_id: int,
    user_categories: list,
) -> Optional[dict]:
    """
    Check if the user has previously assigned a category to this merchant.
    Returns the same dict shape as suggest_category(), or None.
    """
    if not merchant or db is None:
        return None
    try:
        from app.models.merchant_mapping import MerchantCategoryMapping
        mk = normalise_merchant_key(merchant)
        # Fetch all user mappings; try substring match for OCR variance
        mappings = (
            db.query(MerchantCategoryMapping)
            .filter(MerchantCategoryMapping.user_id == user_id)
            .all()
        )
        best = None
        best_score = 0
        for mapping in mappings:
            stored = mapping.merchant_key
            # Score: length of the common substring (longer = better match)
            if stored in mk or mk in stored:
                score = len(stored) if stored in mk else len(mk)
                if score > best_score:
                    best_score = score
                    best = mapping

        if best is None or best.category_id is None:
            return None

        # Verify category still exists in user's list
        cat = next((c for c in user_categories if c.id == best.category_id), None)
        if cat is None:
            return None

        return {
            "category_id": cat.id,
            "category_name": cat.name,
            "matched_type": "learned",
        }
    except Exception:
        return None


def _infer_type(merchant: Optional[str], ocr_snippet: str) -> Optional[str]:
    """
    Return the best-matching category type from _KEYWORD_MAP, or None.
    Checks merchant name first (higher confidence), then OCR text.
    """
    sources = []
    if merchant:
        sources.append((_normalise(merchant), 2))     # weight 2 – direct merchant match
    sources.append((_normalise(ocr_snippet[:400]), 1)) # weight 1 – OCR context

    scores: dict[str, int] = {}
    for text, weight in sources:
        for cat_type, keywords in _KEYWORD_MAP.items():
            for kw in keywords:
                if kw in text:
                    scores[cat_type] = scores.get(cat_type, 0) + weight

    if not scores:
        return None
    return max(scores, key=lambda k: scores[k])


def _match_user_category(
    cat_type: str,
    user_categories: list,
) -> Optional[tuple[int, str]]:
    """
    Find the user's category whose name best matches the inferred type.
    Returns (category_id, category_name) or None.
    """
    synonyms = _SYNONYMS.get(cat_type, [cat_type])

    best_id: Optional[int] = None
    best_name: Optional[str] = None
    best_score = 0

    for cat in user_categories:
        name_norm = _normalise(cat.name)
        score = 0
        for syn in synonyms:
            if syn in name_norm:
                # Longer match = better
                score += len(syn)
        if score > best_score:
            best_score = score
            best_id = cat.id
            best_name = cat.name

    if best_id is not None:
        return best_id, best_name
    return None


def suggest_category(
    merchant: Optional[str],
    ocr_text: str,
    user_categories: list,
    db=None,
    user_id: Optional[int] = None,
) -> Optional[dict]:
    """
    Main entry point.

    Returns a dict like:
        {"category_id": 3, "category_name": "Food & Drink", "matched_type": "food"}
    or None if no suggestion can be made.

    Priority:
      1. Learned mapping (db + user_id required) – user's own confirmed choice
      2. Keyword-based inference
    """
    if not user_categories:
        return None

    # Priority 1: check learned mappings (Phase E)
    if db is not None and user_id is not None:
        learned = _check_learned_mapping(merchant, db, user_id, user_categories)
        if learned is not None:
            return learned

    # Priority 2: keyword inference (Phase C)
    cat_type = _infer_type(merchant, ocr_text)
    if cat_type is None:
        return None

    match = _match_user_category(cat_type, user_categories)
    if match is None:
        return None

    category_id, category_name = match
    return {
        "category_id": category_id,
        "category_name": category_name,
        "matched_type": cat_type,
    }
