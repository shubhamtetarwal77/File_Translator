"""
Image File Handler

Translates text in images using OCR and overlays translated text.

Supports: PNG, JPG, JPEG, BMP, TIFF, WEBP
"""

import platform
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import pytesseract

from core.utils import is_translatable


# Tesseract path
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
        # parents[2] is your project root
        project_root = Path(__file__).resolve().parents[2]
        fonts_dir = project_root / "fonts"

        print("PROJECT ROOT:", project_root)
        print("FONTS DIR:", fonts_dir)
        print("TARGET LANG FOR FONT:", target_lang)

        if target_lang in ["hi", "mr", "ne", "sa"]:
            candidates = [
                fonts_dir / "NotoSansDevanagari-Regular.ttf",
                fonts_dir / "NotoSansDevanagari-VariableFont_wdth,wght.ttf",
                project_root / "NotoSansDevanagari-Regular.ttf",
                project_root / "NotoSansDevanagari-VariableFont_wdth,wght.ttf",
                Path("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"),
                Path("/usr/share/fonts/truetype/noto/NotoSansDevanagariUI-Regular.ttf"),
                Path("/usr/share/fonts/opentype/noto/NotoSansDevanagari-Regular.ttf"),
                Path("C:/Windows/Fonts/mangal.ttf"),
            ]
        else:
            candidates = [
                fonts_dir / "NotoSans-Regular.ttf",
                Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
                Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
                Path("C:/Windows/Fonts/arial.ttf"),
            ]

        for font_path in candidates:
            if font_path.exists():
                print("USING FONT:", font_path)
                return str(font_path)

        raise RuntimeError(
            f"No suitable font found for target language '{target_lang}'.\n\n"
            f"Put your Hindi font here:\n{fonts_dir / 'NotoSansDevanagari-Regular.ttf'}\n\n"
            "Recommended: create a folder named 'fonts' in your project root, "
            "then place NotoSansDevanagari-Regular.ttf inside it."
        )

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
            # OCR language should match the source image language.
            # Your barley image is English.
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

        # Upscale helps OCR detect small text
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
                "On Streamlit Cloud, add these to packages.txt:\n"
                "tesseract-ocr\n"
                "tesseract-ocr-eng"
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

        # Safely detect target language from your TranslationEngine
        target_lang = (
            getattr(translator, "target_lang", None)
            or getattr(translator, "target", None)
            or getattr(translator, "target_language", None)
            or "hi"
        )

        print("TRANSLATOR OBJECT:", translator)
        print("DETECTED TARGET LANG:", target_lang)

        font_path = self._get_font_path(target_lang)

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
            except Exception as e:
                print("Translation failed for:", block_text)
                print("Error:", e)
                translated = block_text

            if not translated:
                translated = block_text

            print("ORIGINAL:", block_text)
            print("TRANSLATED:", translated)

            block_width = max(5, x1 - x0)
            block_height = max(5, y1 - y0)

            padding = 3

            erase_box = [
                max(0, x0 - padding),
                max(0, y0 - padding),
                min(img.width, x1 + padding),
                min(img.height, y1 + padding),
            ]

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
        Group OCR words by line instead of by huge Tesseract block.
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
            sorted_words = sorted(line["words"], key=lambda item: item[0])
            text = " ".join(word for _, word in sorted_words).strip()

            if text and is_translatable(text):
                result.append({
                    "text": text,
                    "bbox": tuple(line["bbox"])
                })

        result.sort(key=lambda item: (item["bbox"][1], item["bbox"][0]))

        return result

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
        Reduce font size until translated text fits inside box.
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

        # Final fallback with smallest font
        font = ImageFont.truetype(font_path, size=min_font_size)
        lines = self._wrap_text_to_width(draw, text, font, box_width - 2)

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
        Estimate background color from around OCR box.
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
