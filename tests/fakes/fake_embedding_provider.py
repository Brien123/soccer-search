class FakeEmbeddingProvider:
    def __init__(self, dims: int = 768, value: float = 0.1) -> None:
        self._dims: int = dims
        self._value: float = value
        self.encoded_texts: list[str] = []

    def encode_query(self, text: str) -> list[float]:
        self.encoded_texts.append(text)
        return [self._value] * self._dims
