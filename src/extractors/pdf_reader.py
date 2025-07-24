"""
Extracción de tablas en PDF con pdfplumber y OCR opcional.
"""

import os
import time
from pathlib import Path
from typing import List

import pdfplumber
import pytesseract
from PIL import Image

from ..core.logger import get_logger
from ..core.config import config


class PDFTableExtractor:
    def __init__(self):
        self.log = get_logger(__name__)
        self.cfg = config.processing
        if self.cfg.ocr_enabled:
            try:
                pytesseract.get_tesseract_version()
            except Exception:
                self.log.warning("Tesseract no encontrado; OCR deshabilitado")
                self.cfg.ocr_enabled = False

    # --------------------------------------------------------------- #
    def extract_tables(self, pdf_path: str) -> List[List[List[str]]]:
        self._validate(pdf_path)
        t0 = time.time()
        tables = self._direct_extract(pdf_path)

        if not tables and self.cfg.ocr_enabled:
            self.log.info("Sin tablas directas, probando OCR")
            tables = self._ocr_extract(pdf_path)

        self.log.info(
            f"PDF {Path(pdf_path).name}: {len(tables)} tablas en {time.time()-t0:.2f}s"
        )
        return tables

    # --------------------------------------------------------------- #
    def _validate(self, pdf_path: str) -> None:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(pdf_path)
        if not pdf_path.lower().endswith(".pdf"):
            raise ValueError("No es un PDF")
        if os.path.getsize(pdf_path) / 1_048_576 > self.cfg.max_file_size_mb:
            raise ValueError("Archivo demasiado grande")

    def _direct_extract(self, pdf_path: str):
        tables = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                for table in page.extract_tables():
                    if table and len(table) > 1 and len(table[0]) > 1:
                        tables.append([[c or "" for c in r] for r in table])
        return tables

    def _ocr_extract(self, pdf_path: str):
        """Implementación sencilla vía OCR, heurística de espacios."""
        tables = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                img = page.to_image(resolution=300).original
                text = pytesseract.image_to_string(img, lang=self.cfg.ocr_language)
                current = []
                for line in text.split("\n"):
                    if "\t" in line or "  " in line:
                        cells = [
                            c.strip()
                            for c in line.replace("\t", "  ").split("  ")
                            if c.strip()
                        ]
                        if len(cells) > 1:
                            current.append(cells)
                    elif current:
                        if len(current) > 1:
                            tables.append(current)
                        current = []
                if current and len(current) > 1:
                    tables.append(current)
        return tables
