from __future__ import annotations

import importlib
import pkgutil

from app.modules.body_systems.base import BodySystemModule


class ModuleRegistry:
    _instance: ModuleRegistry | None = None
    _modules: dict[str, BodySystemModule] = {}

    def __new__(cls) -> ModuleRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, module: BodySystemModule) -> None:
        if module.code:
            self._modules[module.code.upper()] = module

    def get(self, code: str) -> BodySystemModule | None:
        return self._modules.get(code.upper())

    def get_all(self) -> list[BodySystemModule]:
        return list(self._modules.values())

    def get_active(self) -> list[BodySystemModule]:
        return [m for m in self._modules.values() if m.is_active]

    def discover_modules(self) -> None:
        package = importlib.import_module("app.modules.body_systems")
        for _, name, is_pkg in pkgutil.iter_modules(
            package.__path__, package.__name__ + "."
        ):
            if is_pkg:
                try:
                    mod = importlib.import_module(name)
                    if hasattr(mod, "MODULE"):
                        module_instance = mod.MODULE
                        if isinstance(module_instance, BodySystemModule):
                            self.register(module_instance)
                except (ImportError, AttributeError):
                    pass


registry = ModuleRegistry()
