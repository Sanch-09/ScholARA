"""
ScholARA — Logger Setup
Uses loguru for structured, colored logging.
"""

import io
import sys
from loguru import logger


def _console_stream():
    """Use UTF-8 on Windows so emoji/log symbols do not crash cp1252 consoles."""
    if sys.platform != "win32":
        return sys.stdout
    buf = getattr(sys.stdout, "buffer", None)
    if buf is None:
        return sys.stdout
    return io.TextIOWrapper(buf, encoding="utf-8", errors="replace", line_buffering=True)


def setup_logger(debug: bool = True):
    """Configure loguru logger."""
    logger.remove()  # Remove default handler

    # Console handler
    level = "DEBUG" if debug else "INFO"
    logger.add(
        _console_stream(),
        colorize=True,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — <level>{message}</level>",
        level=level,
    )

    # File handler (rotating)
    logger.add(
        "logs/scholara.log",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} — {message}",
    )

    logger.info("Logger initialized")
    return logger
