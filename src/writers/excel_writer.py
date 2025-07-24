# src/writers/excel_writer.py

import os
import re
from pathlib import Path
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from ..core.logger import get_logger
from ..core.config import config
import pandas as pd

# 1. Definir el patrón de caracteres inválidos en XML
_INVALID_XML_CHARS_RE = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F]')

# 2. Función de sanitización
def _sanitize_for_excel(value):
    """
    Elimina caracteres de control inválidos para openpyxl/Excel.
    """
    if isinstance(value, str):
        return _INVALID_XML_CHARS_RE.sub('', value)
    return value

class ExcelWriter:
    def __init__(self):
        self.log = get_logger(__name__)
        self.excel_cfg = config.excel
        self.paths_cfg = config.paths

    def write_dataframe(self, df, out_path):
        out_path = self._prepare_path(out_path)
        wb = Workbook()
        ws = wb.active
        ws.title = self.excel_cfg.default_sheet_name

        start_row = 1
        if self.excel_cfg.include_header:
            for c_idx, col in enumerate(df.columns, 1):
                clean_col = _sanitize_for_excel(str(col))
                ws.cell(1, c_idx, clean_col)
            start_row = 2

        for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=False), start_row):
            for c_idx, val in enumerate(row, 1):
                clean = _sanitize_for_excel(val if pd.notna(val) else "")
                ws.cell(r_idx, c_idx, clean)

        if self.excel_cfg.auto_adjust_width:
            for col_idx, col in enumerate(df.columns, 1):
                length = max(len(str(col)), *(len(str(v)) for v in df[col])) + 2
                ws.column_dimensions[ws.cell(1, col_idx).column_letter].width = min(50, max(10, length))

        wb.save(out_path)
        self.log.info(f"Excel guardado → {Path(out_path).name}")
        return out_path

    def write_multiple_dataframes(self, dfs, out_path):
        out_path = self._prepare_path(out_path)
        wb = Workbook()
        wb.remove(wb.active)

        for name, df in dfs.items():
            ws = wb.create_sheet(title=_sanitize_for_excel(name)[:31])

            start = 1
            if self.excel_cfg.include_header:
                for c_idx, col in enumerate(df.columns, 1):
                    clean_col = _sanitize_for_excel(str(col))
                    ws.cell(1, c_idx, clean_col)
                start = 2

            for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=False), start):
                for c_idx, val in enumerate(row, 1):
                    clean = _sanitize_for_excel(val if pd.notna(val) else "")
                    ws.cell(r_idx, c_idx, clean)

            if self.excel_cfg.auto_adjust_width:
                for col_idx, col in enumerate(df.columns, 1):
                    length = max(len(str(col)), *(len(str(v)) for v in df[col])) + 2
                    ws.column_dimensions[ws.cell(1, col_idx).column_letter].width = min(50, max(10, length))

        wb.save(out_path)
        self.log.info(f"Excel multi-hoja guardado → {Path(out_path).name}")
        return out_path

    def _prepare_path(self, path):
        if not path.lower().endswith(".xlsx"):
            path += ".xlsx"
        if not os.path.isabs(path):
            path = os.path.join(self.paths_cfg.output_dir, path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path
