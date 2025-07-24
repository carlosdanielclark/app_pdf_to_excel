"""
Paquete de extractores.
"""
from .pdf_reader import PDFTableExtractor
from .docx_reader import WordTableExtractor

__all__ = ["PDFTableExtractor", "WordTableExtractor"]
