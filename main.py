"""
CLI: orbita extracción → normalización → exportación.
"""

import os
import sys
import time
from pathlib import Path
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.core.logger import get_logger
from src.core.config import config
from src.extractors import PDFTableExtractor, WordTableExtractor
from src.transformers import TableNormalizer
from src.writers import ExcelWriter


def build_converter():
    log = get_logger(__name__)
    return {
        ".pdf": PDFTableExtractor(),
        ".docx": WordTableExtractor(),
        ".doc": WordTableExtractor(),
        "log": log,
        "normalizer": TableNormalizer(),
        "writer": ExcelWriter(),
    }


# ---------------------------------------------------------------------- #
def convert_one(file_path: str, out_path: str | None = None) -> str:
    ctx = build_converter()
    ext = Path(file_path).suffix.lower()
    if ext not in ctx:
        raise ValueError("Extensión no soportada")

    t0 = time.time()
    tables = ctx[ext].extract_tables(file_path)
    if not tables:
        import pandas as pd

        df = pd.DataFrame([["No se encontraron tablas"]], columns=["mensaje"])
        tables = [df.values.tolist()]
    dfs = {
        f"tabla_{i+1}": ctx["normalizer"].normalize_table(t)
        for i, t in enumerate(tables)
    }
    if len(dfs) == 1:
        df = list(dfs.values())[0]
        out_path = ctx["writer"].write_dataframe(
            df, out_path or f"{Path(file_path).stem}_convertido.xlsx"
        )
    else:
        out_path = ctx["writer"].write_multiple_dataframes(
            dfs, out_path or f"{Path(file_path).stem}_convertido.xlsx"
        )

    ctx["log"].info(
        f"{Path(file_path).name} → {Path(out_path).name} "
        f"({len(dfs)} hojas, {time.time()-t0:.2f}s)"
    )
    return out_path


# ---------------------------------------------------------------------- #
def cli():
    parser = argparse.ArgumentParser("pdf_word_to_excel")
    parser.add_argument("input", help="Archivo o directorio de entrada")
    parser.add_argument("-o", "--output", help="Archivo o directorio de salida")
    parser.add_argument("-b", "--batch", action="store_true", help="Procesar carpeta")
    args = parser.parse_args()

    if args.batch:
        in_dir = Path(args.input)
        out_dir = Path(args.output or config.paths.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        processed = []
        for f in in_dir.iterdir():
            if f.suffix.lower() in (".pdf", ".docx", ".doc"):
                try:
                    processed.append(convert_one(str(f), str(out_dir / f"{f.stem}.xlsx")))
                except Exception as e:
                    print(f"Error en {f.name}: {e}")
        print(f"✓ Batch completado → {len(processed)} archivos convertidos")
    else:
        out_file = convert_one(args.input, args.output)
        print(f"✓ Conversión completada → {out_file}")


if __name__ == "__main__":
    cli()
