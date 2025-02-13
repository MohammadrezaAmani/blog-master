from src.base.scheme import BaseCreateScheme, BaseResponseScheme


class LogCreateScheme(BaseCreateScheme): ...


class LogResponseScheme(LogCreateScheme, BaseResponseScheme): ...
