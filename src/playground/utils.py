import glob
import importlib
import inspect
import os
from typing import List


def load_extensions(extension_folder_path: str) -> List:
    extension_files = glob.glob(f"{extension_folder_path}/*/main.py")
    modules = [_loadModule(extension_file) for extension_file in extension_files]
    extensions = [potential_extension[1] for module in modules for potential_extension in inspect.getmembers(module) if inspect.isclass(potential_extension[1])]

    return extensions

def _loadModule(extension_file: str):
    file_name = os.path.basename(extension_file)
    file_path = os.path.dirname(extension_file)
    module_name = f".{file_name.split('.')[0]}"
    package_name = file_path.replace('/', '_')
    module = importlib.import_module(module_name, package=package_name)
    importlib.reload(module)

    return module