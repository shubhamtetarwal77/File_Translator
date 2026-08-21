"""
PDF File Handler
Converts PDF → DOCX first, then translates using the DocxHandler.
Output will always be a .docx file.
"""

import os
from pdf2docx import Converter
from core.docx_handler import DocxHandler


class PdfHandler:
    """Handles translation of .pdf files by converting them to DOCX."""

    def translate(self, input_path, output_path, translator, progress_callback=None):
        """
        1. Convert PDF to an intermediate DOCX
        2. Pass that DOCX to DocxHandler for translation
        """
        # Temporary file for the raw unconverted DOCX
        temp_docx = input_path + "_raw.docx"

        try:
            if progress_callback:
                progress_callback(0.1, "Step 1/2: Converting PDF to DOCX... (this may take a moment)")

            # 1. Convert PDF to DOCX
            cv = Converter(input_path)
            cv.convert(temp_docx)
            cv.close()

            if progress_callback:
                progress_callback(0.3, "Step 2/2: Translating DOCX text...")

            # 2. Translate the generated DOCX using your existing DocxHandler
            docx_handler = DocxHandler()

            # Wrap the progress so DOCX translation fills the remaining 70% of the progress bar
            def docx_progress(p, msg):
                if progress_callback:
                    progress_callback(0.3 + (p * 0.7), msg)

            docx_handler.translate(
                input_path=temp_docx,
                output_path=output_path,  # Final translated DOCX goes here
                translator=translator,
                progress_callback=docx_progress
            )

        except Exception as e:
            raise RuntimeError(f"PDF to DOCX translation failed: {str(e)}")

        finally:
            # 3. Clean up the intermediate un-translated DOCX file
            if os.path.exists(temp_docx):
                try:
                    os.remove(temp_docx)
                except OSError:
                    pass
