"""
CSV File Handler
Translates cell values in CSV files while preserving:
- Column/row structure
- Delimiters (auto-detected)
- Encoding (output always UTF-8)
- Header row (translated as well)
"""

import csv
import chardet
from core.utils import is_translatable


class CsvHandler:
    """Handles translation of .csv files."""

    def translate(self, input_path, output_path, translator, progress_callback=None):
        """Translate all text content in a CSV file."""

        # ─── Detect encoding ───────────────────────────────────────
        with open(input_path, 'rb') as f:
            raw_data = f.read()

        detection = chardet.detect(raw_data)
        encoding = detection.get('encoding', 'utf-8') or 'utf-8'
        confidence = detection.get('confidence', 0)

        # Fall back to utf-8 if low confidence
        if confidence < 0.7:
            encoding = 'utf-8'

        # ─── Detect delimiter ──────────────────────────────────────
        try:
            sample = raw_data.decode(encoding, errors='replace')[:10240]
            dialect = csv.Sniffer().sniff(sample)
            delimiter = dialect.delimiter
        except Exception:
            delimiter = ','

        # ─── Read CSV ──────────────────────────────────────────────
        try:
            with open(input_path, 'r', encoding=encoding, errors='replace', newline='') as f:
                reader = csv.reader(f, delimiter=delimiter)
                rows = list(reader)
        except Exception:
            # Fallback: try utf-8
            with open(input_path, 'r', encoding='utf-8', errors='replace', newline='') as f:
                reader = csv.reader(f)
                rows = list(reader)

        if not rows:
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                pass
            return

        # ─── Translate ─────────────────────────────────────────────
        total_cells = sum(len(row) for row in rows)
        processed = 0

        for row_idx in range(len(rows)):
            for col_idx in range(len(rows[row_idx])):
                cell_value = rows[row_idx][col_idx]
                if cell_value and isinstance(cell_value, str) and is_translatable(cell_value):
                    rows[row_idx][col_idx] = translator.translate_text(cell_value)

                processed += 1
                if progress_callback and processed % 200 == 0:
                    progress_callback(
                        processed / total_cells,
                        f"Translating CSV... ({processed}/{total_cells} cells)"
                    )

        # ─── Write CSV ─────────────────────────────────────────────
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        if progress_callback:
            progress_callback(1.0, "CSV translation complete!")