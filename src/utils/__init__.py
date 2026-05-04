"""
Utility: logging centralizzato per l'applicazione.
"""
import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Restituisce un logger configurato con handler su stdout.

    Args:
        name: Nome del modulo/componente che richiede il logger.

    Returns:
        Logger configurato.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
