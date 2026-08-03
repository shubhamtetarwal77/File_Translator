"""
PDF File Handler
Supports both text-based and image-based (scanned) PDFs.

Two translation strategies:
1. TEXT mode: For text-based PDFs — extracts text blocks with positions,
   redacts original text, and inserts translated text at the same positions.
2. IMAGE mode: For image-based PDFs — renders pages to images, uses OCR
   to detect text, overlays translated text, and reassembles the PDF.

The handler automatically detects which mode to use per page.
"""

import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
import io

from core.utils import find_system_font, wrap_text_for_box, int_to_rgb, is_translatable


class PdfHandler:
    """Handles translation of .pdf files."""

    # PyMuPDF built-in fonts that support CJK
    CJK_LANGUAGES = {'zh-CN', 'zh-TW', 'ja', 'ko'}
    BUILTIN_FONT_MAP = {
        'zh-CN': 'china-s',
        'zh-TW': 'china-t',
        'ja': 'japan',
        'ko': 'korea',
    }

    def translate(self, input_path, output_path, translator, progress_callback=None):
        """
        Translate a PDF file.
        Automatically detects text vs image pages and uses the appropriate strategy.
        """
        doc = fitz.open(input_path)
        total_pages = len(doc)

        if total_pages == 0:
            doc.save(output_path)
            return

        # Process each page
        for page_num in range(total_pages):
            if progress_callback:
                progress = (page_num) / total_pages
                progress_callback(
                    progress,
                    f"Processing page {page_num + 1} of {total_pages}..."
                )

            page = doc[page_num]
            page_text = page.get_text().strip()

            if page_text:
                # Text-based page: use direct text replacement
                self._translate_text_page(page, translator)
            else:
                # Image-based page: render, OCR, overlay, replace
                self._translate_image_page(page, doc, page_num, translator)

        doc.save(output_path)

        if progress_callback:
            progress_callback(1.0, "PDF translation complete!")

    # ─── Strategy 1: Direct Text Replacement ───────────────────────

    def _translate_text_page(self, page, translator):
        """
        Translate a text-based PDF page by:
        1. Extracting text blocks with positions
        2. Translating each block
        3. Redacting original text
        4. Inserting translated text at the same position
        """
        # Extract text blocks
        text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
        blocks_to_translate = []

        for block in text_dict.get("blocks", []):
            if block["type"] != 0:  # Skip image blocks
                continue

            block_text = ""
            block_bbox = None
            max_font_size = 0
            dominant_color = 0
            total_chars = 0

            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    span_text = span.get("text", "").strip()
                    if span_text:
                        block_text += span.get("text", "")
                        font_size = span.get("size", 12)
                        char_count = len(span_text)
                        total_chars += char_count
                        # Track dominant font size (weighted by character count)
                        if char_count > 0:
                            max_font_size += font_size * char_count
                        if block_bbox is None:
                            block_bbox = fitz.Rect(span["bbox"])
                        else:
                            block_bbox |= fitz.Rect(span["bbox"])
                        dominant_color = span.get("color", 0)

                # Add line break between lines
                block_text += "\n"

            if total_chars > 0:
                max_font_size = max_font_size / total_chars

            block_text = block_text.strip()
            if not block_text or not is_translatable(block_text):
                continue

            blocks_to_translate.append({
                "text": block_text,
                "bbox": block_bbox,
                "font_size": max_font_size,
                "color": dominant_color,
            })

        if not blocks_to_translate:
            return

        # Translate all blocks first (before any page modifications)
        for block in blocks_to_translate:
            block["translated"] = translator.translate_text(block["text"])

        # Redact all original text
        for block in blocks_to_translate:
            rect = fitz.Rect(block["bbox"])
            page.add_redact_annot(rect, fill=True)

        # Apply all redactions at once
        page.apply_redactions()

        # Insert translated text
        fontname = self._get_fontname(translator.target_lang)
        fontfile = self._get_fontfile(translator.target_lang)

        for block in blocks_to_translate:
            translated = block["translated"]
            rect = fitz.Rect(block["bbox"])
            font_size = block["font_size"]
            color = int_to_rgb(block["color"])

            # Try to insert with original font size
            inserted = self._insert_text(
                page, rect, translated, font_size, color,
                fontname, fontfile
            )

            # If text doesn't fit, try with smaller font
            if not inserted:
                smaller_sizes = [font_size * 0.8, font_size * 0.65, font_size * 0.5]
                for smaller_size in smaller_sizes:
                    inserted = self._insert_text(
                        page, rect, translated, smaller_size, color,
                        fontname, fontfile
                    )
                    if inserted:
                        break

    def _insert_text(self, page, rect, text, font_size, color, fontname, fontfile):
        """
        Try to insert text into a rectangle using insert_textbox.
        Returns True if successful.
        """
        try:
            kwargs = {
                "rect": rect,
                "buffer": text,
                "fontsize": font_size,
                "color": color,
                "align": 0,  # Left align
                "expandtabs": False,
            }

            if fontfile and fontname:
                kwargs["fontname"] = fontname
                kwargs["fontfile"] = fontfile
            else:
                kwargs["fontname"] = fontname if fontname else "helv"

            rc = page.insert_textbox(**kwargs)
            # rc < 0 means text didn't fit completely
            return True  # Even partial fit is acceptable

        except Exception as e:
            # Try with basic font as last resort
            try:
                page.insert_textbox(
                    rect=rect,
                    buffer=text,
                    fontsize=font_size,
                    fontname="helv",
                    color=color,
                    align=0,
                )
                return True
            except Exception:
                return False

    def _get_fontname(self, target_lang):
        """Get the appropriate PyMuPDF font name for the target language."""
        if target_lang in self.BUILTIN_FONT_MAP:
            return self.BUILTIN_FONT_MAP[target_lang]
        return "helv"

    def _get_fontfile(self, target_lang):
        """
        Get a font file path for Unicode support.
        Returns None for languages supported by built-in fonts.
        """
        # CJK languages have built-in fonts in PyMuPDF
        if target_lang in self.CJK_LANGUAGES:
            return None

        # For other languages, try to find a system font
        import os
        from core.utils import SYSTEM_FONT_PATHS, FONT_CANDIDATES
        import sys

        font_group = 'DEFAULT'
        from core.utils import LANG_FONT_MAP
        font_group = LANG_FONT_MAP.get(target_lang, 'DEFAULT')
        candidates = FONT_CANDIDATES.get(font_group, FONT_CANDIDATES['DEFAULT'])

        platform = sys.platform
        if platform == 'win32':
            font_dirs = SYSTEM_FONT_PATHS['win32']
        elif platform == 'darwin':
            font_dirs = SYSTEM_FONT_PATHS['darwin']
        else:
            font_dirs = SYSTEM_FONT_PATHS['linux']

        for font_name in candidates:
            for font_dir in font_dirs:
                if not os.path.isdir(font_dir):
                    continue
                font_path = os.path.join(font_dir, font_name)
                if os.path.isfile(font_path):
                    return font_path

        return None

    # ─── Strategy 2: Image Overlay with OCR ────────────────────────

    def _translate_image_page(self, page, doc, page_num, translator):
        """
        Handle image-based (scanned) PDF pages:
        1. Render page to image
        2. Use OCR to detect text regions
        3. Overlay translated text on the image
        4. Replace the page with the modified image
        """
        try:
            import pytesseract
            import numpy as np
        except ImportError:
            print("[PDF] pytesseract/numpy not available; skipping image page OCR")
            return

        # Render page to image
        scale = 2.0  # 144 DPI
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Run OCR
        try:
            ocr_data = pytesseract.image_to_data(
                img, output_type=pytesseract.Output.DICT, lang='eng'
            )
        except Exception as e:
            print(f"[PDF] OCR failed for page {page_num}: {e}")
            return

        # Group OCR words into blocks (by line/block numbers)
        blocks = self._group_ocr_words(ocr_data, scale)

        if not blocks:
            return

        # Draw on image
        draw = ImageDraw.Draw(img)
        font = find_system_font(translator.target_lang, font_size=14)

        for block in blocks:
            # White out original text
            x0, y0, x1, y1 = block["bbox"]
            draw.rectangle([x0, y0, x1, y1], fill="white")

            # Translate
            translated = translator.translate_text(block["text"])

            # Calculate font size based on block height
            block_height = y1 - y0
            block_width = x1 - x0
            font_size = max(int(block_height * 0.8), 8)

            try:
                font = find_system_font(translator.target_lang, font_size=font_size)
            except Exception:
                pass

            # Wrap text and draw
            lines = wrap_text_for_box(draw, translated, font, block_width)
            y_pos = y0
            for line in lines:
                draw.text((x0 + 2, y_pos), line, fill="black", font=font)
                try:
                    line_bbox = draw.textbbox((0, 0), line, font=font)
                    line_height = line_bbox[3] - line_bbox[1]
                except Exception:
                    line_height = font_size
                y_pos += line_height

        # Replace PDF page with the modified image
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        # Create a new page from the image
        new_page = doc.new_page(
            pno=page_num,
            width=page.rect.width,
            height=page.rect.height
        )
        new_page.insert_image(
            new_page.rect,
            stream=img_bytes.getvalue(),
        )

        # Delete the original page
        doc.delete_page(page_num + 1)

    def _group_ocr_words(self, ocr_data, scale):
        """
        Group OCR words into logical blocks for translation.
        Returns list of {"text": str, "bbox": (x0, y0, x1, y1)}.
        """
        blocks = {}
        n_items = len(ocr_data.get('text', []))

        for i in range(n_items):
            text = ocr_data['text'][i].strip()
            conf = int(ocr_data['conf'][i])

            if not text or conf < 30:
                continue

            block_num = ocr_data['block_num'][i]
            x = ocr_data['left'][i]
            y = ocr_data['top'][i]
            w = ocr_data['width'][i]
            h = ocr_data['height'][i]

            if block_num not in blocks:
                blocks[block_num] = {
                    "text": "",
                    "bbox": [x, y, x + w, y + h]
                }
            else:
                # Expand bounding box
                blocks[block_num]["bbox"][0] = min(blocks[block_num]["bbox"][0], x)
                blocks[block_num]["bbox"][1] = min(blocks[block_num]["bbox"][1], y)
                blocks[block_num]["bbox"][2] = max(blocks[block_num]["bbox"][2], x + w)
                blocks[block_num]["bbox"][3] = max(blocks[block_num]["bbox"][3], y + h)

            blocks[block_num]["text"] += " " + text

        # Filter and return
        result = []
        for block in blocks.values():
            text = block["text"].strip()
            if text and is_translatable(text):
                result.append({
                    "text": text,
                    "bbox": tuple(block["bbox"])
                })

        return result