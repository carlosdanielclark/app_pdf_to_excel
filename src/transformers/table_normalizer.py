"""
Limpieza y tipado automático de tablas (pandas).
"""

import re, unicodedata
import pandas as pd
from ..core.logger import get_logger
from ..core.config import config

class TableNormalizer:
    def __init__(self, mappings=None):
        self.log = get_logger(__name__)
        self.cfg = config._config["normalization"]
        # Mapeo para Ficha de Costo
        self.mappings = mappings or {
            "col_0": "codigo",
            "col_1": "descripcion",
            "col_2": "um",
            "col_3": "cantidad",
            "col_4": "precio_unitario",
            "col_5": "importe",
        }
        self.regex = {
            "number": re.compile(r"^[+-]?\d+(?:[.,]\d+)*$"),
            "currency": re.compile(r"^[€$¥£]?\d+(?:[.,]\d+)*$"),
            "percent": re.compile(r"^\d+(?:[.,]\d+)?%$"),
            "date": re.compile(r"^\d{1,2}[-/\\.]\d{1,2}[-/\\.]\d{2,4}$"),
        }

    def normalize_table(self, raw, name="tabla"):
        if not raw:
            self.log.warning(f"{name} vacía")
            return pd.DataFrame()

        df = pd.DataFrame(raw).replace("", pd.NA)
        if self.cfg["remove_empty_rows"]:
            df = df.dropna(how="all")
        if self.cfg["remove_empty_columns"]:
            df = df.dropna(how="all", axis=1)

        header = df.iloc[0]
        # Detección de encabezado vs datos
        if sum(bool(self.regex["number"].match(str(v))) for v in header) < len(header)*0.4:
            df.columns = [self._clean(h) for h in header]
            df = df.iloc[1:].reset_index(drop=True)
        else:
            df.columns = [f"col_{i}" for i in range(df.shape[1])]

        if self.cfg["handle_merged_cells"]:
            df = df.fillna(method="ffill").fillna("")

        # Tipificación de columnas
        for col in df.columns:
            typ = self._detect_type(df[col])
            try:
                if typ=="number":
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "."), errors="coerce")
                elif typ=="currency":
                    df[col] = df[col].astype(str).str.replace(r"[€$¥£]", "", regex=True).str.replace(",", ".").astype(float)
                elif typ=="percent":
                    df[col] = df[col].astype(str).str.rstrip("%").str.replace(",", ".").astype(float) / 100
                elif typ=="date":
                    df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
            except Exception as e:
                self.log.debug(f"Error tipificando {col}: {e}")

        # Renombrar columnas según mappings
        df = df.rename(columns=self.mappings, errors="ignore")
        return df.reset_index(drop=True)

    def _clean(self, item):
        h = unicodedata.normalize("NFKD", str(item)).strip().lower()
        h = re.sub(r"[ \s]+", "_", h)
        h = re.sub(r"[^\w_]", "", h)
        return h or f"col_{len(h)}"

    def _detect_type(self, col):
        sample = col.dropna().astype(str).head(100)
        for name, pat in self.regex.items():
            if sample.apply(lambda x: bool(pat.match(x))).mean() > 0.6:
                return name
        return "text"
