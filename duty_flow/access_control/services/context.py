from dataclasses import dataclass
from typing import Optional, Set

from django.contrib.auth.models import User

from units.models import Unit


@dataclass
class AccessContext:
    user: User
    user_unit: Optional[Unit] = None
    user_level: Optional[int] = None
    descendant_unit_ids: Set[int] = None

    def __post_init__(self):
        self.descendant_unit_ids = set()

        profile = getattr(self.user, "profile", None)
        if not profile:
            return

        self.user_unit = profile.unit
        self.user_level = profile.level

        if self.user_unit:
            self.descendant_unit_ids = set(self.user_unit.get_descendants_ids())

    @property
    def own_unit_id(self):
        return self.user_unit.id if self.user_unit else None