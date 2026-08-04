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
    """Handles translation of image files with OCR."""

    def _get_font_path(self, target_lang):
        """
        Return a font path that supports the target language.
        """

        project_root = Path.cwd()
        fonts_dir = project_root / "fonts"

        print("========== FONT DEBUG ==========")
        print("CURRENT WORKING DIRECTORY:", Path.cwd())
        print("CURRENT FILE:", Path(__file__).resolve())
        print("FONTS DIR:", fonts_dir)
        print("TARGET LANG:", target_lang)

        if target_lang in ["hi", "mr", "ne", "sa"]:
            candidates = [
                fonts_dir / "NotoSansDevanagari-Regular.ttf",
                Path(__file__).resolve().parent.parent / "fonts" / "NotoSansDevanagari-Regular.ttf",
                Path("/mount/src/file_translator/fonts/NotoSansDevanagari-Regular.ttf"),
                Path("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"),
                Path("/usr/share/fonts/truetype/noto/NotoSansDevanagariUI-Regular.ttf"),
                Path("/usr/share/fonts/opentype/noto/NotoSansDevanagari-Regular.ttf"),
            ]
        elif target_lang in ["ar", "ur", "fa"]:
            candidates = [
                fonts_dir / "NotoNaskhArabic-Regular.ttf",
                Path("/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf"),
                Path("/usr/share/fonts/opentype/noto/NotoNaskhArabic-Regular.ttf"),
            ]
        elif target_lang in ["zh-CN", "zh-TW", "ja", "ko"]:
            candidates = [
                fonts_dir / "NotoSansCJK-Regular.ttc",
                Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            ]
        else:
            candidates = [
                fonts_dir / "NotoSans-Regular.ttf",
                Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
                Path("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf"),
            ]

        for path in candidates:
            print("CHECK FONT:", path, "EXISTS:", path.exists())

            if path.exists():
                print("USING FONT:", path)
                print("========== END FONT DEBUG ==========")
                return str(path)

        print("========== END FONT DEBUG ==========")

        raise RuntimeError(
            f"No suitable font found for target language '{target_lang}'.\n\n"
            f"Expected Hindi font here:\n{fonts_dir / 'NotoSansDevanagari-Regular.ttf'}\n\n"
            "In your GitHub repo, the file must be:\n"
            "fonts/NotoSansDevanagari-Regular.ttf"
        )

    def translate(self, input_path, output_path, translator, progress_callback=None, ocr_lang=None):
        """
        Translate text in an image.

        1. OCR text and positions
        2. Group OCR words into visual rows/chunks
        3. Translate each chunk
        4. Erase original chunk area
        5. Draw translated text using suitable font
        """

        if ocr_lang is None:
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

        # Upscale image for better OCR.
        scale_factor = 2
        ocr_img = img.resize(
            (img.width * scale_factor, img.height * scale_factor),
            Image.LANCZOS,
        )

        if progress_callback:
            progress_callback(0.2, f"Running OCR language: {ocr_lang}...")

        try:
            ocr_data = pytesseract.image_to_data(
                ocr_img,
                lang=ocr_lang,
                output_type=pytesseract.Output.DICT,
                config="--oem 3 --psm 6",
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

        target_lang = (
            getattr(translator, "target_lang", None)
            or getattr(translator, "target", None)
            or getattr(translator, "target_language", None)
            or "hi"
        )

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

            block_width = max(5, x1 - x0)
            block_height = max(5, y1 - y0)

            # Skip tiny OCR detections; they usually create messy overlays.
            if block_width < 25 or block_height < 8:
                continue

            # Skip very long noisy OCR blocks.
            # These are often incorrectly merged table/diagram pieces.
            if len(block_text) > 180:
                print("SKIPPING LONG OCR BLOCK:", block_text)
                continue

            try:
                translated = translator.translate_text(block_text)
            except Exception as e:
                print("Translation failed for:", block_text)
                print("Error:", e)
                translated = block_text

            if not translated:
                translated = block_text

            padding = 2

            erase_box = [
                max(0, x0 - padding),
                max(0, y0 - padding),
                min(img.width, x1 + padding),
                min(img.height, y1 + padding),
            ]

            box_width = erase_box[2] - erase_box[0]
            box_height = erase_box[3] - erase_box[1]

            # Use smaller font for dense infographics.
            is_title = y0 < img.height * 0.15 and block_width > img.width * 0.35

            if is_title:
                max_size = min(34, max(14, int(block_height * 0.75)))
            else:
                max_size = min(15, max(6, int(block_height * 0.60)))

            font, lines = self._fit_text_to_box(
                draw=draw,
                text=translated,
                font_path=font_path,
                box_width=box_width,
                box_height=box_height,
                max_font_size=max_size,
                min_font_size=5,
            )

            if not lines:
                continue

            bg_color = self._estimate_background_color(img, erase_box)
            draw.rectangle(erase_box, fill=bg_color)

            y_pos = erase_box[1]

            for line in lines:
                if y_pos > erase_box[3]:
                    break

                draw.text(
                    (erase_box[0] + 1, y_pos),
                    line,
                    fill=(0, 0, 0),
                    font=font,
                )

                bbox = draw.textbbox((0, 0), line, font=font)
                line_height = bbox[3] - bbox[1]
                y_pos += line_height + 2

            if progress_callback:
                progress_callback(
                    0.4 + 0.55 * (idx + 1) / total_blocks,
                    f"Translating text block {idx + 1} of {total_blocks}...",
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
        Group OCR words by visual rows and split large horizontal gaps.
        Better for infographics than relying only on Tesseract line_num.
        """

        words = []
        n_items = len(ocr_data.get("text", []))

        for i in range(n_items):
            text = ocr_data["text"][i].strip()

            if not text:
                continue

            try:
                conf = float(ocr_data["conf"][i])
            except Exception:
                conf = -1

            if conf < 45:
                continue

            x = int(ocr_data["left"][i] / scale_factor)
            y = int(ocr_data["top"][i] / scale_factor)
            w = int(ocr_data["width"][i] / scale_factor)
            h = int(ocr_data["height"][i] / scale_factor)

            if w < 3 or h < 3:
                continue

            words.append(
                {
                    "text": text,
                    "x": x,
                    "y": y,
                    "w": w,
                    "h": h,
                    "cx": x + w / 2,
                    "cy": y + h / 2,
                }
            )

        if not words:
            return []

        words.sort(key=lambda item: item["cy"])

        rows = []

        for word in words:
            placed = False

            for row in rows:
                avg_y = sum(w["cy"] for w in row) / len(row)
                avg_h = sum(w["h"] for w in row) / len(row)

                if abs(word["cy"] - avg_y) <= max(6, avg_h * 0.6):
                    row.append(word)
                    placed = True
                    break

            if not placed:
                rows.append([word])

        result = []

        for row in rows:
            row.sort(key=lambda item: item["x"])

            current_chunk = []

            for word in row:
                if not current_chunk:
                    current_chunk.append(word)
                    continue

                prev = current_chunk[-1]
                gap = word["x"] - (prev["x"] + prev["w"])
                avg_h = sum(w["h"] for w in current_chunk) / len(current_chunk)

                # Split line when there is a large horizontal gap.
                if gap > max(28, avg_h * 2.5):
                    self._add_ocr_chunk_to_result(current_chunk, result)
                    current_chunk = [word]
                else:
                    current_chunk.append(word)

            if current_chunk:
                self._add_ocr_chunk_to_result(current_chunk, result)

        result.sort(key=lambda item: (item["bbox"][1], item["bbox"][0]))

        return result

    def _add_ocr_chunk_to_result(self, chunk, result):
        """
        Convert one OCR word chunk into one translatable block.
        """

        if not chunk:
            return

        text = " ".join(w["text"] for w in chunk).strip()

        if not text or not is_translatable(text):
            return

        x0 = min(w["x"] for w in chunk)
        y0 = min(w["y"] for w in chunk)
        x1 = max(w["x"] + w["w"] for w in chunk)
        y1 = max(w["y"] + w["h"] for w in chunk)

        result.append(
            {
                "text": text,
                "bbox": (x0, y0, x1, y1),
            }
        )

    def _wrap_text_to_width(self, draw, text, font, max_width):
        """
        Wrap text to fit inside max_width.
        Also breaks very long words character-by-character if needed.
        """

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

                word_bbox = draw.textbbox((0, 0), word, font=font)
                word_width = word_bbox[2] - word_bbox[0]

                if word_width <= max_width:
                    current_line = word
                else:
                    chunk = ""

                    for ch in word:
                        test_chunk = chunk + ch
                        ch_bbox = draw.textbbox((0, 0), test_chunk, font=font)
                        ch_width = ch_bbox[2] - ch_bbox[0]

                        if ch_width <= max_width:
                            chunk = test_chunk
                        else:
                            if chunk:
                                lines.append(chunk)
                            chunk = ch

                    current_line = chunk

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
        Estimate background color around OCR box.
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
