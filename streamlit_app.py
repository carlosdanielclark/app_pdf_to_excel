"""
UI Streamlit para usuarios finales.
"""

import os
import sys
from pathlib import Path
import io
import time

import streamlit as st
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.core.config import config
from src.core.logger import get_logger
from src.extractors import PDFTableExtractor, WordTableExtractor
from src.transformers import TableNormalizer
from src.writers import ExcelWriter


log = get_logger(__name__)
st.set_page_config(page_title=config.streamlit.title,
                   page_icon=config.streamlit.icon,
                   layout=config.streamlit.layout)

st.title("📊 Convertidor PDF/Word a Excel")

uploaded = st.file_uploader("Elige un archivo", type=["pdf", "docx", "doc"])

if uploaded:
    size_mb = len(uploaded.getvalue()) / 1_048_576
    if size_mb > config.processing.max_file_size_mb:
        st.error("Archivo demasiado grande")
        st.stop()

    # Guardar temporal
    temp_file = Path(config.paths.temp_dir) / uploaded.name
    temp_file.write_bytes(uploaded.getvalue())

    ext = temp_file.suffix.lower()
    extractor = PDFTableExtractor() if ext == ".pdf" else WordTableExtractor()
    tables = extractor.extract_tables(str(temp_file))

    st.info(f"Encontradas {len(tables)} tablas")
    normalizer = TableNormalizer()
    dfs = {f"tabla_{i+1}": normalizer.normalize_table(t) for i, t in enumerate(tables)}

    for name, df in dfs.items():
        st.subheader(name)
        st.dataframe(df.head(50), use_container_width=True)

    writer = ExcelWriter()
    if len(dfs) == 1:
        excel_path = writer.write_dataframe(
            list(dfs.values())[0],
            f"{temp_file.stem}_convertido.xlsx",
        )
    else:
        excel_path = writer.write_multiple_dataframes(
            dfs, f"{temp_file.stem}_convertido.xlsx"
        )

    with open(excel_path, "rb") as fp:
        st.download_button("📥 Descargar Excel",
                           data=fp.read(),
                           file_name=Path(excel_path).name)

    temp_file.unlink(missing_ok=True)
