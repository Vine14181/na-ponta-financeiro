import socket

ALLOWED_HOSTS = {

    "script.google.com",

    "sheets.googleapis.com",
    "www.googleapis.com",
    "oauth2.googleapis.com",
    "accounts.google.com",

    "generativelanguage.googleapis.com",
    "api.anthropic.com",

    "www.pierre.finance",
    "pierre.finance",
}

ALLOWED_SUFFIXES = (

    "script.googleusercontent.com",
)

ALLOWED_LITERALS = {"127.0.0.1", "::1", "localhost"}

_original_getaddrinfo = None
_active = False

class BlockedHostError(OSError):
    pass

def _is_allowed(host: str) -> bool:
    if not host:
        return False
    h = host.strip().rstrip(".").lower()
    if h in ALLOWED_LITERALS:
        return True
    if h in ALLOWED_HOSTS:
        return True
    for suffix in ALLOWED_SUFFIXES:
        if h == suffix or h.endswith("." + suffix):
            return True
    return False

def _guarded_getaddrinfo(host, *args, **kwargs):
    if not _is_allowed(str(host)):
        raise BlockedHostError(
            f"[netguard] Conexão bloqueada para host não autorizado: {host!r}. "
            f"O Na Ponta só se comunica com sua planilha, o Pierre e a IA configurada."
        )
    return _original_getaddrinfo(host, *args, **kwargs)

def activate():
    global _original_getaddrinfo, _active
    if _active:
        return
    _original_getaddrinfo = socket.getaddrinfo
    socket.getaddrinfo = _guarded_getaddrinfo
    _active = True

def is_active() -> bool:
    return _active
