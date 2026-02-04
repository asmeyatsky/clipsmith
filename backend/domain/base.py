from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any, TypeVar, Generic
import uuid


@dataclass(frozen=True, kw_only=True)
class Entity:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class ValueObject:
    pass
