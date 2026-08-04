"""
Image File Handler

Translates text in images using OCR and overlays translated text.

Supports: PNG, JPG, JPEG, BMP, TIFF, WEBP
"""

import os
import platform
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import pytesseract

from core.utils import is_translatable


if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"


class ImageHandler:
    """Handles translation of image files with text OCR."""

        def _get_font_path(self, target_lang):
        """
        Return a font path that supports the target language.
        For Hindi, force Noto Sans Devanagari from project/fonts.
        """

        # image_handler.py is inside core/handlers/
        # parents[2] = project root
        project_root = Path(__file__).resolve().parents[2]

        fonts_dir = project_root / "fonts"

        if target_lang in ["hi", "mr", "ne", "sa"]:
            font_path = fonts_dir / "NotoSansDevanagari-Regular.ttf"

            if font_path.exists():
                return str(font_path)

            raise RuntimeError(
                f"Hindi font not found at: {font_path}\n"
                "Create a fonts folder in your project root and put "
                "NotoSansDevanagari-Regular.ttf inside it."
            )

        # fallback for English/Latin
        fallback_font = fonts_dir / "NotoSans-Regular.ttf"

        if fallback_font.exists():
            return str(fallback_font)

        return None
    def translate(self, input_path, output_path, translator, progress_callback=None, ocr_lang=None):
        """
        Translate text in an image.

        Flow:
        1. OCR text and positions
        2. Group OCR words into lines
        3. Translate each line
        4. Erase original line area
        5. Draw translated text using suitable font
        """

        if ocr_lang is None:
            # OCR language should be source image language.
            # Your sample image is English.
            ocr_lang = "eng"

        if progress_callback:
            progress_callback(0.1, "Opening image...")

        img = Image.open(input_path)

        if img.mode != "RGB":
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "RGBA":
                background.paste(img, mask=img.split()[3])
            else:
                background.paste(img)
            img = background

        # Optional upscale helps OCR on small infographic text
        original_size = img.size
        scale_factor = 2

        ocr_img = img.resize(
            (img.width * scale_factor, img.height * scale_factor),
            Image.LANCZOS
        )

        if progress_callback:
            progress_callback(0.2, f"Running OCR language: {ocr_lang}...")

        try:
            ocr_data = pytesseract.image_to_data(
                ocr_img,
                lang=ocr_lang,
                output_type=pytesseract.Output.DICT,
                config="--oem 3 --psm 6"
            )
        except Exception as e:
            raise RuntimeError(
                f"OCR failed: {e}\n\n"
                "Make sure Tesseract OCR is installed.\n"
                "For Streamlit Cloud, add tesseract packages in packages.txt."
            )

        if progress_callback:
            progress_callback(0.35, "Grouping OCR text...")

        text_blocks = self._group_ocr_words_by_line(ocr_data, scale_factor)

        if not text_blocks:
            img.save(output_path)
            if progress_callback:
                progress_callback(1.0, "No text detected in image.")
            return

        draw = ImageDraw.Draw(img)

        target_lang = getattr(translator, "target_lang", None)
        if target_lang is None:
            target_lang = getattr(translator, "target", "en")

        font_path = self._get_font_path(target_lang)

        if font_path is None:
            raise RuntimeError(
                f"No suitable font found for target language '{target_lang}'. "
                "Install Noto fonts, especially NotoSansDevanagari for Hindi."
            )

        total_blocks = len(text_blocks)

        if progress_callback:
            progress_callback(0.4, "Translating detected text...")

        for idx, block in enumerate(text_blocks):
            x0, y0, x1, y1 = block["bbox"]
            block_text = block["text"].strip()

            if not block_text or not is_translatable(block_text):
                continue

            # Translate safely
            try:
                translated = translator.translate_text(block_text)
            except Exception:
                # Do not write API errors into the image.
                translated = block_text

            if not translated:
                translated = block_text

            block_width = max(5, x1 - x0)
            block_height = max(5, y1 - y0)

            padding = 3

            erase_box = [
                max(0, x0 - padding),
                max(0, y0 - padding),
                min(img.width, x1 + padding),
                min(img.height, y1 + padding),
            ]

            # Estimate local background color instead of always white
            bg_color = self._estimate_background_color(img, erase_box)

            draw.rectangle(erase_box, fill=bg_color)

            box_width = erase_box[2] - erase_box[0]
            box_height = erase_box[3] - erase_box[1]

            font, lines = self._fit_text_to_box(
                draw=draw,
                text=translated,
                font_path=font_path,
                box_width=box_width,
                box_height=box_height,
                max_font_size=max(10, int(block_height * 1.1)),
                min_font_size=6,
            )

            y_pos = erase_box[1]

            for line in lines:
                if y_pos > erase_box[3]:
                    break

                draw.text(
                    (erase_box[0] + 1, y_pos),
                    line,
                    fill=(0, 0, 0),
                    font=font
                )

                bbox = draw.textbbox((0, 0), line, font=font)
                line_height = bbox[3] - bbox[1]
                y_pos += line_height + 2

            if progress_callback:
                progress_callback(
                    0.4 + 0.55 * (idx + 1) / total_blocks,
                    f"Translating text line {idx + 1} of {total_blocks}..."
                )

        output_ext = output_path.rsplit(".", 1)[-1].upper()

        if output_ext == "JPG":
            output_ext = "JPEG"

        if output_ext not in ("PNG", "JPEG", "BMP", "TIFF", "WEBP"):
            output_ext = "PNG"

        img.save(output_path, format=output_ext, quality=95)

        if progress_callback:
            progress_callback(1.0, "Image translation complete!")

    def _group_ocr_words_by_line(self, ocr_data, scale_factor=1):
        """
        Group OCR words by line instead of by large Tesseract block.

        This is much better for posters, screenshots, and infographics.
        """

        lines = {}

        n_items = len(ocr_data.get("text", []))

        for i in range(n_items):
            text = ocr_data["text"][i].strip()

            if not text:
                continue

            try:
                conf = float(ocr_data["conf"][i])
            except Exception:
                conf = -1

            if conf < 35:
                continue

            block_num = ocr_data["block_num"][i]
            par_num = ocr_data["par_num"][i]
            line_num = ocr_data["line_num"][i]

            key = (block_num, par_num, line_num)

            x = int(ocr_data["left"][i] / scale_factor)
            y = int(ocr_data["top"][i] / scale_factor)
            w = int(ocr_data["width"][i] / scale_factor)
            h = int(ocr_data["height"][i] / scale_factor)

            if key not in lines:
                lines[key] = {
                    "words": [],
                    "bbox": [x, y, x + w, y + h]
                }

            lines[key]["words"].append((x, text))

            lines[key]["bbox"][0] = min(lines[key]["bbox"][0], x)
            lines[key]["bbox"][1] = min(lines[key]["bbox"][1], y)
            lines[key]["bbox"][2] = max(lines[key]["bbox"][2], x + w)
            lines[key]["bbox"][3] = max(lines[key]["bbox"][3], y + h)

        result = []

        for line in lines.values():
            # Sort words left-to-right
            sorted_words = sorted(line["words"], key=lambda item: item[0])
            text = " ".join(word for _, word in sorted_words).strip()

            if text and is_translatable(text):
                result.append({
                    "text": text,
                    "bbox": tuple(line["bbox"])
                })

        # Process top-to-bottom
        result.sort(key=lambda item: (item["bbox"][1], item["bbox"][0]))

        return result

    def _get_font_path(self, target_lang):
        """
        Return suitable font path for target language.
        Add your own bundled fonts if deploying to Streamlit Cloud.
        """

        base_dir = os.path.dirname(os.path.abspath(__file__))

        candidates = []

        if target_lang in ["hi", "mr", "ne", "sa"]:
            candidates.extend([
                os.path.join(base_dir, "../../fonts/NotoSansDevanagari-Regular.ttf"),
                os.path.join(base_dir, "../fonts/NotoSansDevanagari-Regular.ttf"),
                "fonts/NotoSansDevanagari-Regular.ttf",
                "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
                "/usr/share/fonts/truetype/noto/NotoSansDevanagariUI-Regular.ttf",
                "/usr/share/fonts/opentype/noto/NotoSansDevanagari-Regular.ttf",
                "C:/Windows/Fonts/mangal.ttf",
            ])
        elif target_lang in ["ar", "ur", "fa"]:
            candidates.extend([
                "fonts/NotoNaskhArabic-Regular.ttf",
                "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
                "/usr/share/fonts/opentype/noto/NotoNaskhArabic-Regular.ttf",
            ])
        elif target_lang in ["zh-CN", "zh-TW", "ja", "ko"]:
            candidates.extend([
                "fonts/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            ])

        # General fallback fonts
        candidates.extend([
            "fonts/NotoSans-Regular.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ])

        for path in candidates:
            normalized = os.path.abspath(path) if not os.path.isabs(path) else path
            if os.path.exists(normalized):
                return normalized

        return None

    def _wrap_text_to_width(self, draw, text, font, max_width):
        words = text.split()

        if not words:
            return []

        lines = []
        current_line = ""

        for word in words:
            test_line = word if not current_line else current_line + " " + word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]

            if width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines

    def _fit_text_to_box(
        self,
        draw,
        text,
        font_path,
        box_width,
        box_height,
        max_font_size=24,
        min_font_size=6,
    ):
        """
        Reduce font size until wrapped translated text fits inside box.
        """

        box_width = max(5, box_width)
        box_height = max(5, box_height)

        for size in range(max_font_size, min_font_size - 1, -1):
            font = ImageFont.truetype(font_path, size=size)
            lines = self._wrap_text_to_width(draw, text, font, box_width - 2)

            total_height = 0

            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                total_height += bbox[3] - bbox[1] + 2

            if total_height <= box_height:
                return font, lines

        # Final fallback
        font = ImageFont.truetype(font_path, size=min_font_size)
        lines = self._wrap_text_to_width(draw, text, font, box_width - 2)

        # Clip number of lines to box height
        clipped_lines = []
        used_height = 0

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_height = bbox[3] - bbox[1] + 2

            if used_height + line_height > box_height:
                break

            clipped_lines.append(line)
            used_height += line_height

        return font, clipped_lines

    def _estimate_background_color(self, img, box):
        """
        Estimate background color from around the OCR box.
        This looks better than always using white.
        """

        x0, y0, x1, y1 = box

        sample_points = [
            (max(0, x0 - 2), max(0, y0 - 2)),
            (min(img.width - 1, x1 + 2), max(0, y0 - 2)),
            (max(0, x0 - 2), min(img.height - 1, y1 + 2)),
            (min(img.width - 1, x1 + 2), min(img.height - 1, y1 + 2)),
        ]

        colors = []

        for point in sample_points:
            try:
                colors.append(img.getpixel(point))
            except Exception:
                pass

        if not colors:
            return (255, 255, 255)

        r = sum(c[0] for c in colors) // len(colors)
        g = sum(c[1] for c in colors) // len(colors)
        b = sum(c[2] for c in colors) // len(colors)

        return (r, g, b)
