"""
Logging estructurado con Loguru, rotación y JSON.
"""

import sys
import os
from pathlib import Path
from loguru import logger
from datetime import datetime

from .config import config


class LoggerManager:
    """Inicializa Loguru según la configuración YAML."""
    _initialized = False

    @classmethod
    def initialize(cls) -> None:
        if cls._initialized:
            return

        cfg = config.logging_config
        paths = config.paths

        # Salida consola -------------------------------------------------
        logger.remove()
        logger.add(
            sys.stdout,
            level=cfg.level.upper(),
            colorize=cfg.format.lower() != "json",
            serialize=cfg.format.lower() == "json",
            format="{time} | {level} | {message}",
        )

        # Salida archivo --------------------------------------------------
        Path(paths.logs_dir).mkdir(parents=True, exist_ok=True)
        logger.add(
            Path(paths.logs_dir) / "app.log",
            level=cfg.level.upper(),
            rotation=cfg.rotation,
            retention=cfg.retention,
            compression="zip",
            serialize=cfg.format.lower() == "json",
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )

        cls._initialized = True
        logger.info("Logging inicializado")


def get_logger(module_name: str):
    LoggerManager.initialize()
    return logger.bind(module=module_name)

class StructuredLogger:
    """
    Envoltorio opcional para añadir métodos de logging estructurado.
    """
    def __init__(self, module_name: str):
        self._logger = get_logger(module_name)

    def info(self, msg: str, **kwargs):
        self._logger.bind(**kwargs).info(msg)

    def error(self, msg: str, **kwargs):
        self._logger.bind(**kwargs).error(msg)

    # Añade otros niveles (debug, warning, etc.) según necesites.
