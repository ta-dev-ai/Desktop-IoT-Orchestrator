from __future__ import annotations

import importlib.util
import shutil
import sys
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class DependencyReport:
    python_ok: bool
    modules: Dict[str, bool] = field(default_factory=dict)
    commands: Dict[str, bool] = field(default_factory=dict)

    @property
    def missing_modules(self) -> List[str]:
        return [name for name, ok in self.modules.items() if not ok]

    @property
    def missing_commands(self) -> List[str]:
        return [name for name, ok in self.commands.items() if not ok]

    @property
    def ok(self) -> bool:
        return self.python_ok and not self.missing_modules and not self.missing_commands

    def summary_lines(self) -> List[str]:
        lines = [f"Python: {'OK' if self.python_ok else 'KO'}"]
        lines.extend(f"Module {name}: {'OK' if ok else 'KO'}" for name, ok in self.modules.items())
        lines.extend(f"Command {name}: {'OK' if ok else 'KO'}" for name, ok in self.commands.items())
        return lines


def check_python_runtime() -> bool:
    return sys.version_info >= (3, 10)


def check_module(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def check_command(command_name: str) -> bool:
    return shutil.which(command_name) is not None


def build_dependency_report() -> DependencyReport:
    modules = {
        "PySide6": check_module("PySide6"),
        "fastapi": check_module("fastapi"),
        "uvicorn": check_module("uvicorn"),
    }

    commands = {
        "mosquitto": check_command("mosquitto"),
        "mosquitto_sub": check_command("mosquitto_sub"),
        "mosquitto_pub": check_command("mosquitto_pub"),
    }

    return DependencyReport(
        python_ok=check_python_runtime(),
        modules=modules,
        commands=commands,
    )

