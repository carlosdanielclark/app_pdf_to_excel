"""
Gestor central de configuración (Singleton).
Lee config/default.yaml, crea rutas de trabajo y expone acceso tipado.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging


@dataclass
class PathsConfig:
    input_dir: str
    output_dir: str
    temp_dir: str
    logs_dir: str


@dataclass
class ProcessingConfig:
    ocr_enabled: bool
    ocr_language: str
    max_file_size_mb: int
    supported_formats: list
    table_detection_threshold: float


@dataclass
class NormalizationConfig:
    remove_empty_rows: bool
    remove_empty_columns: bool
    handle_merged_cells: bool
    standardize_encoding: bool
    max_columns: int


@dataclass
class ExcelConfig:
    include_header: bool
    auto_adjust_width: bool
    number_format: str
    date_format: str
    default_sheet_name: str


@dataclass
class LoggingConfig:
    level: str
    format: str
    rotation: str
    retention: str
    max_size: str


@dataclass
class StreamlitConfig:
    title: str
    icon: str
    layout: str
    theme: str
    max_upload_size: int


@dataclass
class SecurityConfig:
    allowed_extensions: list
    scan_uploads: bool
    sanitize_filenames: bool


class ConfigManager:
    _instance: Optional["ConfigManager"] = None
    _config: Optional[Dict[str, Any]] = None

    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._load_config()

    # ------------------------------------------------------------------ #
    # Internos                                                           #
    # ------------------------------------------------------------------ #
    def _load_config(self) -> None:
        try:
            config_path = self._find_config_file()
            with open(config_path, "r", encoding="utf-8") as file:
                self._config = yaml.safe_load(file)

            # Crear directorios
            self._create_directories()
            logging.info(f"Configuración cargada desde {config_path}")

        except Exception as e:
            logging.error(f"Error cargando configuración: {e}")
            raise

    def _find_config_file(self) -> str:
        for path in (
            "config/default.yaml",
            "../config/default.yaml",
            "../../config/default.yaml",
            Path(__file__).parents[2] / "config" / "default.yaml",
        ):
            if os.path.exists(path):
                return str(path)
        raise FileNotFoundError("No se encontró config/default.yaml")

    def _create_directories(self) -> None:
        for key, path in self._config.get("paths", {}).items():
            if key.endswith("_dir"):
                Path(path).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Propiedades tipadas                                                #
    # ------------------------------------------------------------------ #
    @property
    def paths(self) -> PathsConfig:
        return PathsConfig(**self._config["paths"])

    @property
    def processing(self) -> ProcessingConfig:
        return ProcessingConfig(**self._config["processing"])

    @property
    def normalization(self) -> NormalizationConfig:
        return NormalizationConfig(**self._config["normalization"])

    @property
    def excel(self) -> ExcelConfig:
        return ExcelConfig(**self._config["excel"])

    @property
    def logging_config(self) -> LoggingConfig:
        return LoggingConfig(**self._config["logging"])

    @property
    def streamlit(self) -> StreamlitConfig:
        return StreamlitConfig(**self._config["streamlit"])

    @property
    def security(self) -> SecurityConfig:
        return SecurityConfig(**self._config["security"])

    # Acceso genérico
    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)


# Instancia global accesible
config = ConfigManager()
settings = config
