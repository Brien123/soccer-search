class SetRelevanceJudge:
    def __init__(self, relevant_ids: set[str]) -> None:
        self._relevant_ids: set[str] = set(relevant_ids)

    def is_relevant(self, event_id: str | None) -> bool:
        return event_id is not None and event_id in self._relevant_ids
