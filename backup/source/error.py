# coding: utf-8


class SourceError(Exception):
    pass


class SourceErrors(Exception):
    def __init__(self, message: str, errors: list[Exception]) -> None:
        super(SourceErrors, self).__init__(f"{message}: {[str(e) for e in errors]}")
        self.errors = errors
