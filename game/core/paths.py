"""Path resolution utility for PyInstaller compatibility."""
import os
import sys


def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    
    When running as a PyInstaller bundle, this returns the path relative to 
    the temporary folder created by PyInstaller (_MEIPASS). In development,
    it returns the path relative to the current working directory.
    
    Args:
        relative_path: Path relative to the base directory (either project root
                      or PyInstaller temp directory)
    
    Returns:
        str: Absolute path to the resource
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
