import glob
import importlib
import inspect
import os
from typing import List

from nexus_extensibility import ILogger, LogLevel


def load_extensions(extension_folder_path: str, logger: ILogger) -> List:

    extension_files = glob.glob(f"{extension_folder_path}/*/main.py")
    extensions = []

    for extension_file in extension_files:

        try:
            module = _loadModule(extension_file[len(extension_folder_path) + 1:])
            potential_extensions = [potential_extension[1] for potential_extension in inspect.getmembers(module) if inspect.isclass(potential_extension[1])]

            for potential_extension in potential_extensions:
                extensions.append(potential_extension)

        except Exception as ex:
            logger.log(LogLevel.Debug, f"Unable to load module {extension_file}. Reason: {str(ex)}")

    return extensions

def _loadModule(extension_file: str):
    file_name = os.path.basename(extension_file)
    file_path = os.path.dirname(extension_file)
    module_name = f".{file_name.split('.')[0]}"
    package_name = file_path.replace('/', '_')
    module = importlib.import_module(module_name, package=package_name)
    importlib.reload(module)

    return module
