from dataclasses import dataclass
from .BaseObject import BaseObject, Color, Position


@dataclass
class _GuideFields:
    position: Position
    name: str = None
    color: Color = None


@dataclass
class Guide(BaseObject, _GuideFields):
    def __post_init__(self):
        # Convert dict or list to Position if needed
        if isinstance(self.position, dict):
            self.position = Position(**self.position)
        elif isinstance(self.position, (list, tuple)):
            self.position = Position(*self.position)
        super().__post_init__()
