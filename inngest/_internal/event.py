from __future__ import annotations

from .types import BaseModel


class Event(BaseModel):
    data: dict[str, object] = {}
    id: str = ""
    name: str
    ts: int = 0
    user: dict[str, object] = {}