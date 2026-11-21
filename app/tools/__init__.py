# from app.tools import read, write, bash
# from app.tools.registry import schemas, run_tool

import importlib
import pkgutil

from app.tools.registry import ToolContext, schemas, run_tool

for module_info in pkgutil.iter_modules(__path__):
    if module_info.name != "registry":
        importlib.import_module(f"{__name__}.{module_info.name}")