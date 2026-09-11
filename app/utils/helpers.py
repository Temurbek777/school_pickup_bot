# app/utils/helpers.py
import re

CYRILLIC_TO_LATIN = {
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D',
    'Е': 'E', 'Ё': 'E', 'Ж': 'ZH', 'З': 'Z', 'И': 'I',
    'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N',
    'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T',
    'У': 'U', 'Ф': 'F', 'Х': 'KH', 'Ц': 'TS', 'Ч': 'CH',
    'Ш': 'SH', 'Щ': 'SHCH', 'Ы': 'Y', 'Э': 'E', 'Ю': 'YU', 'Я': 'YA'
}


def normalize_grade(grade_str: str) -> str:
    """
    Normalizes grade inputs:
    '4-B', '4b', '4 B', '4-б', '4Б' -> '4B'
    """
    if not grade_str:
        return ""

    # 1. Convert to uppercase and strip whitespace
    cleaned = grade_str.strip().upper()

    # 2. Replace Cyrillic characters with Latin equivalent
    for cyr, lat in CYRILLIC_TO_LATIN.items():
        cleaned = cleaned.replace(cyr, lat)

    # 3. Remove all hyphens, spaces, and non-alphanumeric chars
    cleaned = re.sub(r'[^A-Z0-9]', '', cleaned)

    return cleaned