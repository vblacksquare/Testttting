
import typing
from dataclasses import dataclass, field


@dataclass
class Product:
    title: str
    path: str
    fields: dict[str, typing.Any] = field(default_factory=dict)
