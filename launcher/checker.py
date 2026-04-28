from __future__ import annotations

import importlib.util
import shutil
import sys
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class DependencyItem:
    category: str
    name: str
    ok: bool
    detail: str

    @property
    def status(self) -> str:
        return "OK" if self.ok else "MISSING"


@dataclass
class DependencyReport:
    python_ok: bool
    items: List[DependencyItem] = field(default_factory=list)

    @property
    def missing_items(self) -> List[DependencyItem]:
        return [item for item in self.items if not item.ok]

    @property
    def ok(self) -> bool:
        return self.python_ok and not self.missing_items

    def summary_lines(self) -> List[str]:
        lines = [
            "Dependency check",
            "================",
            f"Overall status: {'READY' if self.ok else 'ACTION NEEDED'}",
            "",
        ]

        current_category = ""
        for item in self.items:
            if item.category != current_category:
                current_category = item.category
                lines.extend(["", f"{current_category}:"])
            lines.append(f"  [{item.status:<7}] {item.name:<22} {item.detail}")

        if self.missing_items:
            lines.extend(["", "Missing dependencies:"])
            lines.extend(f"  - {item.name}: {item.detail}" for item in self.missing_items)
        else:
            lines.extend(["", "All required dependencies are available."])

        return lines


def check_python_runtime() -> bool:
    return sys.version_info >= (3, 10)


def check_module(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def module_item(display_name: str, module_name: str) -> DependencyItem:
    ok = check_module(module_name)
    detail = "import available" if ok else f"install Python package `{module_name}`"
    return DependencyItem("Python modules", display_name, ok, detail)


def command_item(category: str, display_name: str, command_name: str, hint: str) -> DependencyItem:
    path = shutil.which(command_name)
    ok = path is not None
    detail = path if ok else hint
    return DependencyItem(category, display_name, ok, detail)


def build_dependency_report() -> DependencyReport:
    python_ok = check_python_runtime()
    python_detail = sys.version.split()[0]

    items = [
        DependencyItem(
            "Runtime",
            "Python >= 3.10",
            python_ok,
            python_detail if python_ok else "install Python 3.10 or newer",
        ),
        module_item("PySide6", "PySide6"),
        module_item("FastAPI", "fastapi"),
        module_item("Uvicorn", "uvicorn"),
        command_item("JavaScript tools", "Node.js", "node", "install Node.js to run dashboard checks"),
        command_item("JavaScript tools", "npm", "npm", "install npm with Node.js"),
        command_item("MQTT tools", "Mosquitto broker", "mosquitto", "install Mosquitto or add it to PATH"),
        command_item("MQTT tools", "Mosquitto subscriber", "mosquitto_sub", "install Mosquitto CLI tools"),
        command_item("MQTT tools", "Mosquitto publisher", "mosquitto_pub", "install Mosquitto CLI tools"),
    ]

    return DependencyReport(
        python_ok=python_ok,
        items=items,
    )
