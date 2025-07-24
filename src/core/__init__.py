"""
Módulo core: expone configuración y logging.
"""
from .config import config, settings, ConfigManager
from .logger import get_logger, LoggerManager, StructuredLogger

__all__ = [
    "config",
    "settings",
    "ConfigManager",
    "get_logger",
    "LoggerManager",
    "StructuredLogger",
]
