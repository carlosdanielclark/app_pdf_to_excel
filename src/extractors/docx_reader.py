"""
Extracción de tablas en Word (DOCX/DOC).
"""

import os
import time
from pathlib import Path
from typing import List

from docx import Document
from docx.table import Table as DocxTable

from ..core.logger import get_logger
from ..core.config import config


class WordTableExtractor:
    def __init__(self):
        self.log = get_logger(__name__)
        self.cfg = config.processing

    # --------------------------------------------------------------- #
    def extract_tables(self, doc_path: str) -> List[List[List[str]]]:
        self._validate(doc_path)
        t0 = time.time()

        doc = Document(doc_path)
        tables = [self._table_to_list(t) for t in doc.tables if t.rows]

        self.log.info(
            f"Word {Path(doc_path).name}: {len(tables)} tablas en {time.time()-t0:.2f}s"
        )
        return tables

    # --------------------------------------------------------------- #
    @staticmethod
    def _table_to_list(table: DocxTable):
        return [[cell.text.strip() for cell in row.cells] for row in table.rows]

    def _validate(self, doc_path):
        if not os.path.exists(doc_path):
            raise FileNotFoundError(doc_path)
        if not any(doc_path.lower().endswith(ext) for ext in (".docx", ".doc")):
            raise ValueError("No es un archivo Word")
        if os.path.getsize(doc_path) / 1_048_576 > config.processing.max_file_size_mb:
            raise ValueError("Archivo demasiado grande")
