"""
Shared utility functions: font management, text wrapping, color conversion, etc.
"""

import os
import sys
import urllib.request
from pathlib import Path
from PIL import ImageFont

# ─── Font Cache Directory ──────────────────────────────────────────
FONT_CACHE_DIR = Path.home() / ".file_translator" / "fonts"
FONT_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Map language codes to font families that support them
LANG_FONT_MAP = {
    # CJK languages
    'zh-CN': 'CJK', 'zh-TW': 'CJK', 'ja': 'CJK', 'ko': 'CJK',
    # Indic languages
    'hi': 'INDIC', 'bn': 'INDIC', 'ta': 'INDIC', 'te': 'INDIC',
    'mr': 'INDIC', 'gu': 'INDIC', 'kn': 'INDIC', 'ml': 'INDIC',
    'pa': 'INDIC',
    # Arabic/Hebrew
    'ar': 'ARABIC', 'ur': 'ARABIC', 'fa': 'ARABIC', 'iw': 'HEBREW',
    # Thai
    'th': 'THAI',
    # Georgian
    'ka': 'GEORGIAN',
}

# Common system font paths
SYSTEM_FONT_PATHS = {
    'win32': [
        os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts'),
    ],
    'darwin': [
        '/Library/Fonts', '/System/Library/Fonts',
        os.path.expanduser('~/Library/Fonts'),
    ],
    'linux': [
        '/usr/share/fonts', '/usr/local/share/fonts',
        os.path.expanduser('~/.fonts'),
        os.path.expanduser('~/.local/share/fonts'),
    ],
}

# Font file candidates (in order of preference)
FONT_CANDIDATES = {
    'DEFAULT': [
        'arial.ttf', 'Arial.ttf', 'DejaVuSans.ttf',
        'LiberationSans-Regular.ttf', 'NotoSans-Regular.ttf',
        'FreeSans.ttf', 'Ubuntu-R.ttf',
    ],
    'CJK': [
        'NotoSansCJK-Regular.ttc', 'NotoSansCJKsc-Regular.otf',
        'msyh.ttc', 'msyhbd.ttc',  # Windows Chinese
        'SimSun.ttf', 'SimHei.ttf',  # Windows Chinese
        'PingFang.ttc', 'STHeiti Light.ttc',  # macOS Chinese
        'Hiragino Sans GB.ttc',  # macOS Japanese
        'IPAGothic.ttf',  # Linux Japanese
        'NanumGothic.ttf',  # Linux Korean
        'malgun.ttf', 'malgunbd.ttf',  # Windows Korean
        'AppleGothic.ttf',  # macOS Korean
    ],
    'ARABIC': [
        'NotoSansArabic-Regular.ttf', 'arial.ttf', 'DejaVuSans.ttf',
        'Amiri-Regular.ttf', 'Tahoma.ttf', 'tahoma.ttf',
    ],
    'INDIC': [
        'NotoSansDevanagari-Regular.ttf', 'NotoSansBengali-Regular.ttf',
        'NotoSansTamil-Regular.ttf', 'NotoSansTelugu-Regular.ttf',
        'mangal.ttf', 'Lohit-Devanagari.ttf', 'DejaVuSans.ttf',
    ],
    'THAI': [
        'NotoSansThai-Regular.ttf', 'Tahoma.ttf', 'tahoma.ttf',
        'THSarabunNew.ttf', 'DejaVuSans.ttf',
    ],
    'HEBREW': [
        'NotoSansHebrew-Regular.ttf', 'arial.ttf', 'DejaVuSans.ttf',
        'David.ttf', 'Tahoma.ttf',
    ],
    'GEORGIAN': [
        'NotoSansGeorgian-Regular.ttf', 'DejaVuSans.ttf',
    ],
}


def find_system_font(target_lang='en', font_size=14):
    """
    Find a suitable system font for the target language.
    Returns a PIL ImageFont object.
    """
    font_group = LANG_FONT_MAP.get(target_lang, 'DEFAULT')
    candidates = FONT_CANDIDATES.get(font_group, FONT_CANDIDATES['DEFAULT'])

    # Also try DEFAULT candidates as fallback
    if font_group != 'DEFAULT':
        candidates = candidates + FONT_CANDIDATES['DEFAULT']

    # Get system font directories
    platform = sys.platform
    if platform == 'win32':
        font_dirs = SYSTEM_FONT_PATHS['win32']
    elif platform == 'darwin':
        font_dirs = SYSTEM_FONT_PATHS['darwin']
    else:
        font_dirs = SYSTEM_FONT_PATHS['linux']

    # Search for fonts
    for font_name in candidates:
        for font_dir in font_dirs:
            if not os.path.isdir(font_dir):
                continue

            # Check directly
            font_path = os.path.join(font_dir, font_name)
            if os.path.isfile(font_path):
                try:
                    return ImageFont.truetype(font_path, font_size)
                except Exception:
                    continue

            # Check subdirectories (1 level deep)
            for subdir in os.listdir(font_dir):
                subdir_path = os.path.join(font_dir, subdir)
                if os.path.isdir(subdir_path):
                    font_path = os.path.join(subdir_path, font_name)
                    if os.path.isfile(font_path):
                        try:
                            return ImageFont.truetype(font_path, font_size)
                        except Exception:
                            continue

    # Fallback: PIL default font
    try:
        return ImageFont.truetype("DejaVuSans.ttf", font_size)
    except Exception:
        return ImageFont.load_default()


def wrap_text_for_box(draw, text, font, max_width):
    """
    Wrap text to fit within a given pixel width.
    Returns list of lines.
    """
    if not text:
        return [""]

    words = text.split()
    if not words:
        return [""]

    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        try:
            bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]
        except Exception:
            # Fallback estimation
            text_width = len(test_line) * font.size * 0.6

        if text_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines if lines else [""]


def int_to_rgb(color_int):
    """Convert an integer color (0xRRGGBB) to an (R, G, B) tuple."""
    r = (color_int >> 16) & 0xFF
    g = (color_int >> 8) & 0xFF
    b = color_int & 0xFF
    return (r, g, b)


def rgb_to_hex(rgb_tuple):
    """Convert (R, G, B) tuple to hex string."""
    return '#{:02x}{:02x}{:02x}'.format(*rgb_tuple)


def is_translatable(text):
    """Check if a text string contains translatable content (not just numbers/symbols)."""
    if not text or not text.strip():
        return False

    # Check if there are any alphabetic or CJK characters
    for char in text:
        if char.isalpha():
            return True
        if '\u4e00' <= char <= '\u9fff':  # CJK Unified Ideographs
            return True
        if '\u3040' <= char <= '\u309f':  # Hiragana
            return True
        if '\u30a0' <= char <= '\u30ff':  # Katakana
            return True
        if '\uac00' <= char <= '\ud7af':  # Hangul Syllables
            return True
        if '\u0600' <= char <= '\u06ff':  # Arabic
            return True
        if '\u0900' <= char <= '\u097f':  # Devanagari
            return True

    return False