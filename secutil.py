import re

_PADROES = [
    re.compile(r"(key=)[^&\s\"']+", re.I),
    re.compile(r"(token=)[^&\s\"']+", re.I),
    re.compile(r"sk-ant-[A-Za-z0-9\-_]+"),
    re.compile(r"AIza[A-Za-z0-9\-_]{10,}"),
    re.compile(r"\bsk-[A-Za-z0-9\-_]{16,}"),
    re.compile(r"(Bearer )[A-Za-z0-9\-_\.]+", re.I),
]

def redact(texto) -> str:
    s = str(texto)
    for pad in _PADROES:
        if pad.groups:
            s = pad.sub(r"\1[REDACTED]", s)
        else:
            s = pad.sub("[REDACTED]", s)
    return s
