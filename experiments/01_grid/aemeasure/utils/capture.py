import io
import typing


class OutputCopy(io.StringIO):
    def __init__(self, wrap):
        super().__init__()
        self.wrapped_stream = wrap

    def write(self, __s: str) -> int:
        ret = super().write(__s)
        self.wrapped_stream.write(__s)
        return ret

    def writelines(self, __lines: typing.Iterable[str]) -> None:
        __lines = list(__lines)
        ret = super().writelines(__lines)
        self.wrapped_stream.writelines(__lines)
        return ret