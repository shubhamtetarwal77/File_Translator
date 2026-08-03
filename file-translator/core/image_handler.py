"""
Image File Handler
Translates text in images using OCR (Tesseract) and overlays translated text.
Supports: PNG, JPG, JPEG, BMP, TIFF, WEBP
"""

import os
import platform
import shutil
from PIL import Image, ImageDraw, ImageFont
from core.utils import find_system_font, wrap_text_for_box, is_translatable
import pytesseract


# ─── Smart Tesseract Path Detection ────────────────────────────────
def _configure_tesseract():
    """
    Auto-detect Tesseract executable path.
    - Windows (local): uses default install path if it exists
    - Linux (Streamlit Cloud): finds tesseract from system PATH
    """
    if platform.system() == "Windows":
        windows_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        if os.path.exists(windows_path):
            pytesseract.pytesseract.tesseract_cmd = windows_path
    else:
        # Linux / Mac — locate tesseract installed via packages.txt
        tesseract_path = shutil.which("tesseract")
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path


# Configure once when this module is imported
_configure_tesseract()


class ImageHandler:
    """Handles translation of image files with text (OCR)."""

    def translate(self, input_path, output_path, translator, progress_callback=None):
        """
        Translate text in an image:
        1. OCR to detect text and positions
        2. White out detected text regions
        3. Overlay translated text
        4. Save the modified image
        """
        try:
            import pytesseract
        except ImportError:
            raise ImportError(
                "pytesseract is required for image translation. "
                "Install it: pip install pytesseract. "
                "Also install Tesseract OCR: https://github.com/tesseract-ocr/tesseract"
            )

        if progress_callback:
            progress_callback(0.1, "Opening image...")

        # Open image
        img = Image.open(input_path)

        # Convert to RGB if necessary (for PNG with transparency, etc.)
        if img.mode != 'RGB':
            # Create white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'RGBA':
                background.paste(img, mask=img.split()[3])
            else:
                background.paste(img)
            img = background

        if progress_callback:
            progress_callback(0.2, "Running OCR to detect text...")

        # Run OCR with position data
        try:
            ocr_data = pytesseract.image_to_data(
                img, output_type=pytesseract.Output.DICT
            )
        except pytesseract.TesseractNotFoundError:
            raise RuntimeError(
                "Tesseract OCR is not installed or not found in PATH. "
                "On Streamlit Cloud, add a 'packages.txt' file with 'tesseract-ocr'. "
                "On Windows, install from: https://github.com/UB-Mannheim/tesseract/wiki"
            )
        except Exception as e:
            raise RuntimeError(f"OCR failed: {e}. Make sure Tesseract OCR is installed.")

        if progress_callback:
            progress_callback(0.4, "Translating detected text...")

        # Group OCR words into logical blocks
        text_blocks = self._group_ocr_words(ocr_data)

        if not text_blocks:
            # No text detected, save original
            img.save(output_path)
            if progress_callback:
                progress_callback(1.0, "No text detected in image.")
            return

        # Draw on image
        draw = ImageDraw.Draw(img)
        font = find_system_font(translator.target_lang, font_size=14)

        total_blocks = len(text_blocks)
        for idx, block in enumerate(text_blocks):
            x0, y0, x1, y1 = block["bbox"]
            block_text = block["text"]

            # White out original text area (with small padding)
            padding = 3
            draw.rectangle(
                [x0 - padding, y0 - padding, x1 + padding, y1 + padding],
                fill="white"
            )

            # Translate
            translated = translator.translate_text(block_text)

            # Calculate appropriate font size
            block_height = y1 - y0
            block_width = x1 - x0
            font_size = max(int(block_height * 0.85), 10)

            try:
                font = find_system_font(translator.target_lang, font_size=font_size)
            except Exception:
                pass

            # Wrap text to fit in the block width
            lines = wrap_text_for_box(draw, translated, font, block_width - 4)

            # Draw each line
            y_pos = y0
            for line in lines:
                draw.text((x0 + 2, y_pos), line, fill="black", font=font)
                try:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    line_height = bbox[3] - bbox[1]
                except Exception:
                    line_height = font_size
                y_pos += line_height + 1

            if progress_callback:
                progress_callback(
                    0.4 + 0.5 * (idx + 1) / total_blocks,
                    f"Translating text block {idx + 1} of {total_blocks}..."
                )

        # Save in original format
        output_ext = output_path.rsplit('.', 1)[-1].upper()
        if output_ext == 'JPG':
            output_ext = 'JPEG'
        if output_ext not in ('PNG', 'JPEG', 'BMP', 'TIFF', 'WEBP'):
            output_ext = 'PNG'

        img.save(output_path, format=output_ext, quality=95)

        if progress_callback:
            progress_callback(1.0, "Image translation complete!")

    def _group_ocr_words(self, ocr_data):
        """
        Group OCR-detected words into logical text blocks.
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
                blocks[block_num]["bbox"][0] = min(blocks[block_num]["bbox"][0], x)
                blocks[block_num]["bbox"][1] = min(blocks[block_num]["bbox"][1], y)
                blocks[block_num]["bbox"][2] = max(blocks[block_num]["bbox"][2], x + w)
                blocks[block_num]["bbox"][3] = max(blocks[block_num]["bbox"][3], y + h)

            blocks[block_num]["text"] += " " + text

        # Filter blocks with translatable text
        result = []
        for block in blocks.values():
            text = block["text"].strip()
            if text and is_translatable(text):
                result.append({
                    "text": text,
                    "bbox": tuple(block["bbox"])
                })

        return result
