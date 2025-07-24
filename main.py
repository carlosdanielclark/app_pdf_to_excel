import os, sys, argparse
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.core.logger import get_logger
from src.core.config import config
from src.extractors.pdf_reader import PDFTableExtractor
from src.extractors.docx_reader import WordTableExtractor
from src.transformers.table_normalizer import TableNormalizer
from src.writers.excel_writer import ExcelWriter

def build_converter():
    log = get_logger(__name__)
    return {
        ".pdf": PDFTableExtractor(),
        ".docx": WordTableExtractor(),
        ".doc": WordTableExtractor(),
        "normalizer": TableNormalizer(),
        "writer": ExcelWriter(),
        "log": log
    }

def convert_one(file_path, out_path=None):
    ctx = build_converter()
    ext = Path(file_path).suffix.lower()
    if ext not in ctx:
        raise ValueError("Extensión no soportada")

    tables = ctx[ext].extract_tables(file_path)
    if not tables:
        tables = [[["No se encontraron tablas"]]]

    # Detectar ficha de costo por encabezado
    first_row = tables[0][0] if tables and tables[0] else []
    is_ficha = any("ficha" in str(cell).lower() for cell in first_row)

    dfs = [
        ctx["normalizer"].normalize_table(tbl, name="ficha_costo" if is_ficha else "tabla")
        for tbl in tables
    ]

    if is_ficha and len(dfs) == 1:
        tpl = config._config["excel"]["templates"]["ficha_costo"]
        return ctx["writer"].write_using_template(dfs[0], tpl, out_path or f"{Path(file_path).stem}_ficha.xlsx")
    elif len(dfs) == 1:
        return ctx["writer"].write_dataframe(dfs[0], out_path or f"{Path(file_path).stem}_out.xlsx")
    else:
        multi = {f"tabla_{i+1}": df for i, df in enumerate(dfs)}
        return ctx["writer"].write_multiple_dataframes(multi, out_path or f"{Path(file_path).stem}_out.xlsx")

def cli():
    parser = argparse.ArgumentParser("pdf_word_to_excel")
    parser.add_argument("input", help="Archivo o carpeta")
    parser.add_argument("-o","--output", help="Salida")
    parser.add_argument("-b","--batch", action="store_true", help="Procesar carpeta")
    args = parser.parse_args()

    if args.batch:
        in_dir = Path(args.input)
        out_dir = Path(args.output or config.paths.output_dir)
        out_dir.mkdir(exist_ok=True)
        for f in in_dir.iterdir():
            if f.suffix.lower() in (".pdf", ".docx", ".doc"):
                try:
                    convert_one(str(f), str(out_dir/f"{f.stem}.xlsx"))
                except Exception as e:
                    print(f"Error {f.name}: {e}")
        print("Batch completado")
    else:
        out = convert_one(args.input, args.output)
        print(f"Convertido → {out}")

if __name__ == "__main__":
    cli()
