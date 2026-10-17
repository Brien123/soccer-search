class FakeVector:
    def __init__(self, values: list[float]) -> None:
        self._values: list[float] = values

    def tolist(self) -> list[float]:
        return self._values
