"""
UI Streamlit para usuarios finales.
"""

import os, sys
from pathlib import Path
import streamlit as st
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from src.core.config import config
from src.core.logger import get_logger
from src.extractors.pdf_reader import PDFTableExtractor
from src.extractors.docx_reader import WordTableExtractor
from src.transformers.table_normalizer import TableNormalizer
from src.writers.excel_writer import ExcelWriter

log = get_logger(__name__)
st.set_page_config(
    page_title=config._config["streamlit"]["title"],
    page_icon=config._config["streamlit"]["icon"],
    layout=config._config["streamlit"]["layout"]
)
st.title(config._config["streamlit"]["title"])

uploaded = st.file_uploader("Selecciona PDF o Word", type=config._config["security"]["allowed_extensions"])
if uploaded:
    size_mb = len(uploaded.getvalue())/1_048_576
    if size_mb > config._config["processing"]["max_file_size_mb"]:
        st.error("Archivo demasiado grande"); st.stop()

    tmp = Path(config._config["paths"]["temp_dir"]) / uploaded.name
    tmp.write_bytes(uploaded.getvalue())
    ext = tmp.suffix.lower()
    extractor = PDFTableExtractor() if ext == ".pdf" else WordTableExtractor()
    tables = extractor.extract_tables(str(tmp))

    is_ficha = False
    if tables and tables[0]:
        is_ficha = any("ficha" in str(cell).lower() for cell in tables[0][0])

    normalizer = TableNormalizer()
    dfs = [normalizer.normalize_table(t, name="ficha_costo" if is_ficha else "tabla") for t in tables]

    for i, df in enumerate(dfs, start=1):
        st.subheader(f"Tabla {i}")
        st.dataframe(df.head(50), use_container_width=True)

    writer = ExcelWriter()
    if is_ficha and len(dfs) == 1:
        tpl = config._config["excel"]["templates"]["ficha_costo"]
        out = writer.write_using_template(dfs[0], tpl, f"{tmp.stem}_ficha.xlsx")
    elif len(dfs) == 1:
        out = writer.write_dataframe(dfs[0], f"{tmp.stem}_out.xlsx")
    else:
        multi = {f"tabla_{i}": df for i, df in enumerate(dfs, start=1)}
        out = writer.write_multiple_dataframes(multi, f"{tmp.stem}_out.xlsx")

    with open(out, "rb") as f:
        st.download_button("Descargar Excel", f.read(), file_name=Path(out).name)

    tmp.unlink()
