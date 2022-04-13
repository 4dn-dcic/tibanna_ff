"""Version information."""
import tomlkit
import os
from pathlib import Path

def _get_project_meta():
    try:
        toml_path = Path(__file__).parent.parent.joinpath('pyproject.toml')
        with open(toml_path) as pyproject:
            file_contents = pyproject.read()

        return tomlkit.parse(file_contents)['tool']['poetry']
    except:
        return "version_not_found"
    

pkg_meta = _get_project_meta()

# We use the version from pyproject.toml
__version__ = str(pkg_meta['version'])
