class SourceError(Exception):
    pass


class SourceMultipleError(Exception):
    def __init__(self, message: str, errors: list[Exception]) -> None:
        super().__init__(f"{message}: {[str(e) for e in errors]}")
        self.errors = errors
