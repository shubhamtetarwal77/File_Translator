"""
Image File Handler
Translates text in images using OCR (Tesseract) and overlays translated text.
Supports: PNG, JPG, JPEG, BMP, TIFF, WEBP
"""

import platform
from PIL import Image, ImageDraw, ImageFont

from core.utils import find_system_font, wrap_text_for_box, is_translatable
import pytesseract

# Dynamic Tesseract path for Windows and Linux (Streamlit Cloud)
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
else:
    # For Linux / Streamlit Cloud
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'


class ImageHandler:
    """Handles translation of image files with text (OCR)."""

    def translate(self, input_path, output_path, translator, progress_callback=None, ocr_lang=None):
        """
        Translate text in an image:
        1. OCR to detect text and positions
        2. White out detected text regions
        3. Overlay translated text
        4. Save the modified image
        """
        if ocr_lang is None:
            ocr_lang = 'eng'   # Default to English if no language selected

        try:
            import pytesseract
        except ImportError:
            raise ImportError(
                "pytesseract is required for image translation. "
                "Install it: pip install pytesseract"
            )

        if progress_callback:
            progress_callback(0.1, "Opening image...")

        # Open image
        img = Image.open(input_path)

        # Convert to RGB if necessary
        if img.mode != 'RGB':
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'RGBA':
                background.paste(img, mask=img.split()[3])
            else:
                background.paste(img)
            img = background

        if progress_callback:
            progress_callback(0.2, f"Running OCR (language: {ocr_lang})...")

        # Run OCR with position data + selected language
        try:
            ocr_data = pytesseract.image_to_data(
                img,
                lang=ocr_lang,
                output_type=pytesseract.Output.DICT
            )
        except Exception as e:
            raise RuntimeError(
                f"OCR failed: {e}\n\n"
                "Make sure Tesseract OCR is installed. "
                "On Streamlit Cloud, add 'tesseract-ocr' in packages.txt"
            )

        if progress_callback:
            progress_callback(0.4, "Translating detected text...")

        # Group OCR words into logical blocks
        text_blocks = self._group_ocr_words(ocr_data)

        if not text_blocks:
            img.save(output_path)
            if progress_callback:
                progress_callback(1.0, "No text detected in image.")
            return

        # Draw on image
        draw = ImageDraw.Draw(img)
        total_blocks = len(text_blocks)

        for idx, block in enumerate(text_blocks):
            x0, y0, x1, y1 = block["bbox"]
            block_text = block["text"]

            # White out original text area
            padding = 3
            draw.rectangle(
                [x0 - padding, y0 - padding, x1 + padding, y1 + padding],
                fill="white"
            )

            # Translate
            translated = translator.translate_text(block_text)

            # Calculate font size based on block height
            block_height = y1 - y0
            block_width = x1 - x0
            font_size = max(int(block_height * 0.85), 10)

            try:
                font = find_system_font(translator.target_lang, font_size=font_size)
            except Exception:
                font = ImageFont.load_default()

            # Wrap text to fit box
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

        # Save image
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

        # Filter blocks with meaningful text
        result = []
        for block in blocks.values():
            text = block["text"].strip()
            if text and is_translatable(text):
                result.append({
                    "text": text,
                    "bbox": tuple(block["bbox"])
                })

        return result