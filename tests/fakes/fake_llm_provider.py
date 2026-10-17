class FakeLlmProvider:
    def __init__(self, answer: str = "Fake answer.", model: str = "fake/model") -> None:
        self._answer: str = answer
        self._model: str = model
        self.calls: list[tuple[str, str]] = []

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        return self._answer

    def model_name(self) -> str:
        return self._model
