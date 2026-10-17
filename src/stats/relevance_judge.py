from typing import Protocol


class RelevanceJudge(Protocol):
    def is_relevant(self, event_id: str | None) -> bool: ...
