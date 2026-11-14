import inspect
import json
from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict
    handler: Callable[..., str]

    def schema(self) -> dict:
        return {"type": "function",
                "function": {"name": self.name,
                             "description": self.descriptionm,
                             "parameters": self.parameters}}
    
_REGISTRY: dict[str, Tool] = {}
# _PY_TO_JSON = {str: "string", int: "integer", float: "number", bool: "boolean"}

# def _schema_from_signature(func) -> dict:
#     sig = inspect.signature(func)
#     props, required = {}, []
#     for pname, param in sig.parameters.items():
#         props[pname] = {"type": _PY_TO_JSON.get(param.annotation, "string")}
#         if param.default is inspect.Parameter.empty:
#             required.append(pname)
#     return {"type": "object", "properties": props, "required": required}

def tool(name: str, description: str, parameters: dict):
    def decorator(func):
        _REGISTRY[name] = Tool(
            name=name,
            description=description or "",
            parameters=parameters,
            handler=func
        )
        return func
    return decorator

def schemas() -> list[dict]:
    return [t.schema() for t in _REGISTRY.values()]

def run_tool(name: str, arguments_json: str) -> str:
    t = _REGISTRY.get(name)
    if t is None:
        return f"Error: unknown tool {name!r}"
    try:
        args = json.loads(arguments_json or "{}")
        return t.handler(**args)
    except json.JSONDecodeError as e:
        return f"Error: invalid JSON arguments: {e}"
    except TypeError as e:
        return f"Error: bad arguments for {name}: {e}"
