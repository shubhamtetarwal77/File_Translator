"""
Handler Registry — maps file extensions to their respective handler classes.
"""

from core.docx_handler import DocxHandler
from core.pdf_handler import PdfHandler
from core.excel_handler import ExcelHandler
from core.csv_handler import CsvHandler
from core.pptx_handler import PptxHandler
from core.txt_handler import TxtHandler
from core.image_handler import ImageHandler
from core.subtitle_handler import SubtitleHandler
from core.data_handler import DataHandler

# Registry: file extension → handler instance
_HANDLER_MAP = {
    '.docx': DocxHandler(),
    '.pdf': PdfHandler(),
    '.xlsx': ExcelHandler(),
    '.xls': ExcelHandler(),
    '.csv': CsvHandler(),
    '.pptx': PptxHandler(),
    '.txt': TxtHandler(),
    '.rtf': TxtHandler(),
    '.md': TxtHandler(),
    '.png': ImageHandler(),
    '.jpg': ImageHandler(),
    '.jpeg': ImageHandler(),
    '.bmp': ImageHandler(),
    '.tiff': ImageHandler(),
    '.tif': ImageHandler(),
    '.webp': ImageHandler(),
    '.srt': SubtitleHandler(),
    '.vtt': SubtitleHandler(),
    '.json': DataHandler(),
    '.xml': DataHandler(),
    '.html': DataHandler(),
    '.htm': DataHandler(),
}


def get_handler(file_extension):
    """
    Get the appropriate handler for a file extension.
    Returns handler instance or None if unsupported.
    """
    return _HANDLER_MAP.get(file_extension.lower())


def list_supported_extensions():
    """Return a list of all supported file extensions."""
    return sorted(_HANDLER_MAP.keys())