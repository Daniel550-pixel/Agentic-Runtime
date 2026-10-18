"""Named tool contracts and registry."""

from collections.abc import Callable
from dataclasses import dataclass, field

ToolHandler = Callable[[dict[str, object]], object]


@dataclass(frozen=True, slots=True)
class Tool:
    name: str
    description: str
    handler: ToolHandler


@dataclass(slots=True)
class ToolRegistry:
    _tools: dict[str, Tool] = field(default_factory=dict)

    def register(self, tool: Tool) -> None:
        if not tool.name.strip():
            raise ValueError("Tool name must not be empty.")
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered.")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {name}") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._tools))
