from tests.fakes.fake_vector import FakeVector


class FakeSentenceModel:
    def __init__(self, values: list[float] | None = None) -> None:
        self._values: list[float] = values or [0.1, 0.2, 0.3]
        self.seen_texts: list[str] = []
        self.seen_normalize: bool | None = None

    def encode(self, text: str, normalize_embeddings: bool) -> FakeVector:
        self.seen_texts.append(text)
        self.seen_normalize = normalize_embeddings
        return FakeVector(self._values)
