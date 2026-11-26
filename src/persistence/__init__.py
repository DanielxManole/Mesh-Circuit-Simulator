"""Pachetul `persistence`: save/load proiect + log si cache."""
from .project_io   import save_project, load_project, project_to_dict, dict_to_project
from .logging_cache import setup_logging, autosave, load_autosave, app_data_dir

__all__ = [
    "save_project", "load_project", "project_to_dict", "dict_to_project",
    "setup_logging", "autosave", "load_autosave", "app_data_dir",
]
