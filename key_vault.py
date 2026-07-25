import json
import os
from cryptography.fernet import Fernet, InvalidToken

from config import DATA_DIR, KEYS_FILE, MASTER_KEY_FILE

class VaultError(RuntimeError):
    pass

def _restrict_permissions(path: str):
    try:
        if os.name != "nt":
            os.chmod(path, 0o700 if os.path.isdir(path) else 0o600)
    except Exception:
        pass

def _dpapi_protect(data: bytes) -> bytes | None:
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class DATA_BLOB(ctypes.Structure):
            _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

        def _to_blob(b):
            buf = ctypes.create_string_buffer(b, len(b))
            return DATA_BLOB(len(b), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))), buf

        entrada, _keep = _to_blob(data)
        saida = DATA_BLOB()
        ok = ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(entrada), None, None, None, None, 0, ctypes.byref(saida)
        )
        if not ok:
            return None
        resultado = ctypes.string_at(saida.pbData, saida.cbData)
        ctypes.windll.kernel32.LocalFree(saida.pbData)
        return resultado
    except Exception:
        return None

def _dpapi_unprotect(data: bytes) -> bytes | None:
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class DATA_BLOB(ctypes.Structure):
            _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

        def _to_blob(b):
            buf = ctypes.create_string_buffer(b, len(b))
            return DATA_BLOB(len(b), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))), buf

        entrada, _keep = _to_blob(data)
        saida = DATA_BLOB()
        ok = ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(entrada), None, None, None, None, 0, ctypes.byref(saida)
        )
        if not ok:
            return None
        resultado = ctypes.string_at(saida.pbData, saida.cbData)
        ctypes.windll.kernel32.LocalFree(saida.pbData)
        return resultado
    except Exception:
        return None

_DPAPI_PREFIX = b"DPAPI1:"

class KeyVault:

    def __init__(self):
        self._fernet = None
        self._load_failed = False
        self._ensure_master_key()

    def _ensure_master_key(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        _restrict_permissions(DATA_DIR)

        if os.path.exists(MASTER_KEY_FILE):
            with open(MASTER_KEY_FILE, "rb") as f:
                bruto = f.read()
            if bruto.startswith(_DPAPI_PREFIX):
                master_key = _dpapi_unprotect(bruto[len(_DPAPI_PREFIX):])
                if master_key is None:

                    raise VaultError(
                        "Não foi possível abrir a chave-mestra nesta conta/máquina. "
                        "As chaves precisam ser reconfiguradas em Configurações."
                    )
            else:

                master_key = bruto
                self._fernet = Fernet(master_key)
                self._store_master_key(master_key)
                return
        else:
            master_key = Fernet.generate_key()
            self._store_master_key(master_key)

        self._fernet = Fernet(master_key)

    def _store_master_key(self, master_key: bytes):
        protegida = _dpapi_protect(master_key)
        conteudo = (_DPAPI_PREFIX + protegida) if protegida is not None else master_key
        with open(MASTER_KEY_FILE, "wb") as f:
            f.write(conteudo)
        _restrict_permissions(MASTER_KEY_FILE)

        if os.name == "nt":
            try:
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(MASTER_KEY_FILE, 0x02)
            except Exception:
                pass

    def _load_store(self) -> dict:
        if not os.path.exists(KEYS_FILE):
            return {}
        try:
            with open(KEYS_FILE, "rb") as f:
                encrypted = f.read()
            decrypted = self._fernet.decrypt(encrypted)
            return json.loads(decrypted.decode("utf-8"))
        except (InvalidToken, ValueError, json.JSONDecodeError) as e:
            self._load_failed = True
            raise VaultError(
                f"O cofre de chaves existe mas não pôde ser aberto ({type(e).__name__}). "
                f"Para proteger suas chaves, o app não vai sobrescrevê-lo."
            )

    def _save_store(self, store: dict):
        data = json.dumps(store).encode("utf-8")
        encrypted = self._fernet.encrypt(data)
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(KEYS_FILE, "wb") as f:
            f.write(encrypted)
        _restrict_permissions(KEYS_FILE)

    def save_key(self, name: str, value: str):
        store = self._load_store()
        store[name] = value
        self._save_store(store)

    def get_key(self, name: str) -> str | None:
        try:
            store = self._load_store()
        except VaultError:
            return None
        return store.get(name)

    def delete_key(self, name: str) -> bool:
        try:
            store = self._load_store()
        except VaultError:
            return False
        if name in store:
            del store[name]
            self._save_store(store)
            return True
        return False

    def list_keys(self) -> list[str]:
        try:
            return list(self._load_store().keys())
        except VaultError:
            return []

    def has_key(self, name: str) -> bool:
        try:
            return name in self._load_store()
        except VaultError:
            return False

    def mask_key(self, name: str) -> str:
        key = self.get_key(name)
        if not key:
            return ""
        if len(key) <= 4:
            return "●" * len(key)
        return "●" * (len(key) - 4) + key[-4:]
