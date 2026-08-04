"""
Data File Handler
Translates .json, .xml, and .html files while preserving:
- JSON structure and data types
- XML tags and attributes
- HTML tags, attributes, and structure
"""

import json
import re
from core.utils import is_translatable


class DataHandler:
    """Handles translation of structured data files (JSON, XML, HTML)."""

    def translate(self, input_path, output_path, translator, progress_callback=None):
        """Translate a data file based on its extension."""
        ext = input_path.rsplit('.', 1)[-1].lower()

        if ext == 'json':
            self._translate_json(input_path, output_path, translator, progress_callback)
        elif ext == 'xml':
            self._translate_xml(input_path, output_path, translator, progress_callback)
        elif ext in ('html', 'htm'):
            self._translate_html(input_path, output_path, translator, progress_callback)
        else:
            # Default: treat as text
            self._translate_json(input_path, output_path, translator, progress_callback)

    # ─── JSON ───────────────────────────────────────────────────────

    def _translate_json(self, input_path, output_path, translator, progress_callback=None):
        """
        Translate JSON file — recursively translate all string values
        while preserving the structure, keys, and data types.
        """
        with open(input_path, 'r', encoding='utf-8', errors='replace') as f:
            data = json.load(f)

        self._item_count = 0

        def translate_value(value):
            """Recursively translate string values in the JSON structure."""
            if isinstance(value, str) and is_translatable(value):
                self._item_count += 1
                if progress_callback and self._item_count % 50 == 0:
                    progress_callback(
                        min(self._item_count / max(self._item_count, 1), 0.95),
                        f"Translating JSON value {self._item_count}..."
                    )
                return translator.translate_text(value)
            elif isinstance(value, dict):
                return {k: translate_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [translate_value(item) for item in value]
            return value

        translated_data = translate_value(data)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(translated_data, f, ensure_ascii=False, indent=2)

        if progress_callback:
            progress_callback(1.0, "JSON translation complete!")

    # ─── XML ────────────────────────────────────────────────────────

    def _translate_xml(self, input_path, output_path, translator, progress_callback=None):
        """
        Translate XML file — translate text content of elements
        while preserving tags and attributes.
        """
        import xml.etree.ElementTree as ET

        try:
            tree = ET.parse(input_path)
        except ET.ParseError:
            # Fallback: treat as text
            with open(input_path, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(translator.translate_text(text))
            return

        root = tree.getroot()
        self._xml_count = 0

        def translate_element(elem):
            """Recursively translate element text content."""
            # Translate direct text
            if elem.text and is_translatable(elem.text.strip()):
                elem.text = translator.translate_text(elem.text)
                self._xml_count += 1

            # Translate tail text (text after closing tag)
            if elem.tail and is_translatable(elem.tail.strip()):
                elem.tail = translator.translate_text(elem.tail)
                self._xml_count += 1

            # Process children
            for child in elem:
                translate_element(child)

            if progress_callback and self._xml_count % 50 == 0:
                progress_callback(0.5, f"Translating XML elements... ({self._xml_count})")

        translate_element(root)

        tree.write(output_path, encoding='unicode', xml_declaration=True)

        if progress_callback:
            progress_callback(1.0, "XML translation complete!")

    # ─── HTML ───────────────────────────────────────────────────────

    def _translate_html(self, input_path, output_path, translator, progress_callback=None):
        """
        Translate HTML file — translate visible text content
        while preserving all tags, attributes, and structure.
        """
        try:
            from bs4 import BeautifulSoup, Comment, NavigableString
        except ImportError:
            raise ImportError("beautifulsoup4 is required for HTML translation.")

        with open(input_path, 'r', encoding='utf-8', errors='replace') as f:
            soup = BeautifulSoup(f, 'html.parser')

        # Tags whose content should NOT be translated
        SKIP_TAGS = {'script', 'style', 'code', 'pre', 'kbd', 'var', 'samp'}

        # Attributes that might contain translatable text
        TRANSLATABLE_ATTRS = {'title', 'alt', 'placeholder', 'aria-label', 'value'}

        self._html_count = 0

        def translate_text_nodes(element):
            """Recursively translate text nodes in the HTML tree."""
            if isinstance(element, Comment):
                return

            if element.name in SKIP_TAGS:
                return

            for child in list(element.children):
                if isinstance(child, NavigableString) and not isinstance(child, Comment):
                    text = str(child).strip()
                    if text and is_translatable(text):
                        translated = translator.translate_text(str(child))
                        child.replace_with(NavigableString(translated))
                        self._html_count += 1

                elif hasattr(child, 'children'):
                    translate_text_nodes(child)

            # Translate translatable attributes
            if hasattr(element, 'attrs'):
                for attr in TRANSLATABLE_ATTRS:
                    if attr in element.attrs and is_translatable(element.attrs[attr]):
                        element.attrs[attr] = translator.translate_text(element.attrs[attr])

            if progress_callback and self._html_count % 50 == 0:
                progress_callback(0.5, f"Translating HTML content... ({self._html_count})")

        translate_text_nodes(soup)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))

        if progress_callback:
            progress_callback(1.0, "HTML translation complete!")