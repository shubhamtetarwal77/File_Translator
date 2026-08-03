"""
Text File Handler
Translates .txt, .rtf, and .md files while preserving:
- Line structure
- Markdown syntax (code blocks preserved)
- Basic formatting
"""

import chardet
from core.utils import is_translatable


class TxtHandler:
    """Handles translation of .txt, .rtf, and .md files."""

    def translate(self, input_path, output_path, translator, progress_callback=None):
        """Translate a text/markdown file."""

        # Detect file extension for special handling
        ext = input_path.rsplit('.', 1)[-1].lower() if '.' in input_path else 'txt'

        # ─── Read file with encoding detection ─────────────────────
        with open(input_path, 'rb') as f:
            raw_data = f.read()

        detection = chardet.detect(raw_data)
        encoding = detection.get('encoding', 'utf-8') or 'utf-8'

        try:
            text = raw_data.decode(encoding, errors='replace')
        except Exception:
            text = raw_data.decode('utf-8', errors='replace')

        if not text.strip():
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            return

        # ─── Translate based on format ─────────────────────────────
        if ext == 'md':
            translated_text = self._translate_markdown(text, translator, progress_callback)
        else:
            translated_text = self._translate_plain_text(text, translator, progress_callback)

        # ─── Write output ──────────────────────────────────────────
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated_text)

        if progress_callback:
            progress_callback(1.0, "Text file translation complete!")

    def _translate_plain_text(self, text, translator, progress_callback=None):
        """Translate plain text line by line."""
        lines = text.split('\n')
        total = len(lines)

        for i in range(total):
            if is_translatable(lines[i]):
                lines[i] = translator.translate_text(lines[i])

            if progress_callback and (i + 1) % 20 == 0:
                progress_callback(
                    (i + 1) / total,
                    f"Translating line {i + 1} of {total}..."
                )

        return '\n'.join(lines)

    def _translate_markdown(self, text, translator, progress_callback=None):
        """
        Translate markdown text while preserving:
        - Code blocks (``` ... ```)
        - Inline code (`...`)
        - Markdown syntax (#, *, -, etc.)
        - Links and images
        """
        lines = text.split('\n')
        total = len(lines)
        in_code_block = False

        for i in range(total):
            line = lines[i]

            # Track code block boundaries
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue

            # Skip code block content
            if in_code_block:
                continue

            # Skip empty lines
            if not line.strip():
                continue

            # Skip lines that are only markdown syntax
            stripped = line.strip()
            if stripped in ('---', '***', '___', ''):
                continue

            # Translate the content, preserving leading markdown syntax
            lines[i] = self._translate_markdown_line(line, translator)

            if progress_callback and (i + 1) % 20 == 0:
                progress_callback(
                    (i + 1) / total,
                    f"Translating markdown line {i + 1} of {total}..."
                )

        return '\n'.join(lines)

    def _translate_markdown_line(self, line, translator):
        """
        Translate a single markdown line, preserving syntax prefix.
        E.g., "# Hello World" → "# [translated]"
        """
        # Extract leading markdown syntax
        prefix = ""
        rest = line

        # Headers
        if rest.startswith('#'):
            idx = 0
            while idx < len(rest) and rest[idx] == '#':
                idx += 1
            if idx < len(rest) and rest[idx] == ' ':
                prefix = rest[:idx + 1]
                rest = rest[idx + 1:]
            else:
                prefix = rest[:idx]
                rest = rest[idx:]

        # List items
        elif rest.startswith('- ') or rest.startswith('* ') or rest.startswith('+ '):
            prefix = rest[:2]
            rest = rest[2:]

        # Numbered lists
        elif len(rest) > 0 and rest[0].isdigit():
            idx = 0
            while idx < len(rest) and (rest[idx].isdigit() or rest[idx] == '.'):
                idx += 1
            if idx < len(rest) and rest[idx] == ' ':
                prefix = rest[:idx + 1]
                rest = rest[idx + 1:]

        # Blockquotes
        elif rest.startswith('> '):
            prefix = "> "
            rest = rest[2:]

        if is_translatable(rest):
            translated = translator.translate_text(rest)
            return prefix + translated

        return line