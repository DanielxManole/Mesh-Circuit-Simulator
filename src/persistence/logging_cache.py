"""
Logging si cache (autosave). Scrie totul in folderul de utilizator:
  Windows: %APPDATA%\\SimulatorCircuiteElectrice\\
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional


APP_FOLDER = "SimulatorCircuiteElectrice"


def app_data_dir() -> str:
    """Folder unde aplicatia poate scrie log si cache (cu fallback la cwd)."""
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    path = os.path.join(base, APP_FOLDER)
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        path = os.path.join(os.getcwd(), APP_FOLDER)
        os.makedirs(path, exist_ok=True)
    return path


def setup_logging() -> str:
    """Configureaza logging la fisier (rotire zilnica simpla prin nume)."""
    folder = app_data_dir()
    today = datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(folder, f"app-{today}.log")
    logger = logging.getLogger()
    if logger.handlers:
        return log_path
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.info("=== Simulator pornit ===")
    return log_path


def autosave(scene) -> Optional[str]:
    """Salveaza starea curenta in cache.json. Returneaza calea (sau None)."""
    from .project_io import project_to_dict
    try:
        path = os.path.join(app_data_dir(), "cache.json")
        data = project_to_dict(scene)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path
    except Exception as ex:
        logging.getLogger().warning(f"Autosave esuat: {ex}")
        return None


def load_autosave(scene) -> bool:
    from .project_io import dict_to_project
    path = os.path.join(app_data_dir(), "cache.json")
    if not os.path.isfile(path):
        return False
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        dict_to_project(data, scene)
        return True
    except Exception as ex:
        logging.getLogger().warning(f"Nu am putut restaura cache-ul: {ex}")
        return False
