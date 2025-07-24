"""
Limpieza y tipado automático de tablas (pandas).
"""

import re
import unicodedata
from typing import List, Dict
import pandas as pd
import numpy as np

from ..core.logger import get_logger
from ..core.config import config


class TableNormalizer:
    def __init__(self, column_mappings: Dict[str, str] | None = None):
        self.log = get_logger(__name__)
        self.cfg = config.normalization
        self.mappings = column_mappings or {}

        self.regex = {
            "number": re.compile(r"^[+-]?\d+(?:[.,]\d+)*$"),
            "currency": re.compile(r"^[€$¥£]?\d+(?:[.,]\d+)*$"),
            "percent": re.compile(r"^\d+(?:[.,]\d+)?%$"),
            "date": re.compile(r"^\d{1,2}[-/\\.]\d{1,2}[-/\\.]\d{2,4}$"),
        }

    # ---------------------------------------------------------------- #
    def normalize_table(self, raw: List[List[str]], name: str = "tabla") -> pd.DataFrame:
        if not raw:
            self.log.warning(f"{name} vacía")
            return pd.DataFrame()

        df = pd.DataFrame(raw).replace("", pd.NA)

        if self.cfg.remove_empty_rows:
            df = df.dropna(how="all")
        if self.cfg.remove_empty_columns:
            df = df.dropna(how="all", axis=1)

        # Headers
        if self._is_header(df.iloc[0]):
            df.columns = self._clean_headers(df.iloc[0])
            df = df.iloc[1:].reset_index(drop=True)
        else:
            df.columns = [f"col_{i}" for i in range(df.shape[1])]

        # Ffill celdas fusionadas
        if self.cfg.handle_merged_cells:
            df = df.fillna(method="ffill").fillna("")

        # Tipificación
        for col in df.columns:
            coltype = self._detect_column_type(df[col])
            try:
                if coltype == "number":
                    df[col] = pd.to_numeric(
                        df[col].astype(str).str.replace(",", "."), errors="coerce"
                    )
                elif coltype == "currency":
                    df[col] = (
                        df[col]
                        .astype(str)
                        .str.replace(r"[€$¥£]", "", regex=True)
                        .str.replace(",", ".")
                        .astype(float)
                    )
                elif coltype == "percent":
                    df[col] = (
                        df[col]
                        .astype(str)
                        .str.replace("%", "")
                        .str.replace(",", ".")
                        .astype(float)
                        / 100.0
                    )
                elif coltype == "date":
                    df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
            except Exception as e:
                self.log.debug(f"Columna {col}: {e}")

        # Renombrar por mapeo
        if self.mappings:
            df = df.rename(columns=self.mappings, errors="ignore")

        return df.reset_index(drop=True)

    # ---------------------------------------------------------------- #
    def _is_header(self, row: pd.Series) -> bool:
        numbers = sum(bool(self.regex["number"].match(str(v))) for v in row)
        return numbers < len(row) * 0.4  # 60 % no numérico ⇒ probable header

    def _clean_headers(self, row: pd.Series):
        headers = []
        for item in row:
            h = unicodedata.normalize("NFKD", str(item)).strip().lower()
            h = re.sub(r"[ \\s]+", "_", h)          # espacios
            h = re.sub(r"[^\\w_]", "", h)           # símbolos
            headers.append(h or f"col_{len(headers)}")
        # Sin duplicados
        dedup = []
        for h in headers:
            base, i = h, 1
            while h in dedup:
                h = f"{base}_{i}"
                i += 1
            dedup.append(h) 
        return dedup

    def _detect_column_type(self, col: pd.Series) -> str:
        sample = col.dropna().astype(str).head(100)
        if sample.empty:
            return "text"
        for t, pat in self.regex.items():
            if sample.apply(lambda x: bool(pat.match(x))).mean() > 0.6:
                return t
        return "text"
