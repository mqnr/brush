from datetime import tzinfo
from dateutil import parser as timeparser
from dateutil import tz
import humanize


class DueInfo:
    def __init__(self, due_at: str, timezone: str | tzinfo):
        self.timezone = tz.gettz(timezone) if isinstance(timezone, str) else timezone

        self.exists = bool(due_at)
        self.object = timeparser.isoparse(due_at) if self.exists else None
        self.humanized = (
            humanize.naturaldate(self.object.astimezone(self.timezone)).capitalize()
            if self.exists
            else None
        )

    def __str__(self):
        return f"{self.humanized}, {self.object.astimezone(self.timezone):%H:%M}"
