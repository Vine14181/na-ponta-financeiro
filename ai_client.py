import requests

from key_vault import KeyVault
from secutil import redact

CLAUDE_MODEL = "claude-opus-4-8"

GEMINI_MODEL = "gemini-flash-latest"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
HTTP_TIMEOUT = 120
MAX_TOKENS = 16000

KEY_NAMES = ["custom_api", "custom_api_2"]

class AIError(RuntimeError):
    pass

def _detect_provider(key: str) -> str:
    if key.startswith("sk-ant-"):
        return "anthropic"
    if key.startswith("AIza"):
        return "gemini"
    if key.startswith("sk-"):
        return "anthropic"
    return "gemini"

class AIClient:

    def __init__(self):
        self._vault = KeyVault()
        self.last_key_used: str = ""
        self.last_provider: str = ""

    def _available_keys(self) -> list[tuple[str, str]]:
        keys = []
        for name in KEY_NAMES:
            value = self._vault.get_key(name)
            if value:
                keys.append((name, value.strip()))
        return keys

    @property
    def is_configured(self) -> bool:
        return bool(self._available_keys())

    def generate(self, prompt: str, system: str = None,
                 history: list[tuple[str, str]] = None,
                 prefer_provider: str = None) -> str:
        keys = self._available_keys()
        if not keys:
            raise AIError(
                "Nenhuma chave configurada. Adicione sua chave em "
                "Configurações → API Personalizada 1."
            )

        if prefer_provider:
            keys.sort(key=lambda nk: 0 if _detect_provider(nk[1]) == prefer_provider else 1)

        erros = []
        for name, key in keys:
            provider = _detect_provider(key)
            apelido = "principal" if name == "custom_api" else "reserva"
            try:
                if provider == "anthropic":
                    texto = self._call_claude(key, prompt, system, history)
                else:
                    texto = self._call_gemini(key, prompt, system, history)
                self.last_key_used = name
                self.last_provider = provider
                return texto
            except AIError as e:
                erros.append(f"{apelido} ({provider}): {e}")
                continue

        raise AIError("Todas as chaves falharam — " + " | ".join(erros))

    def _call_claude(self, key: str, prompt: str, system: str,
                     history: list[tuple[str, str]]) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=key)

        messages = []
        for role, text in (history or []):
            messages.append({
                "role": "user" if role == "user" else "assistant",
                "content": text,
            })
        messages.append({"role": "user", "content": prompt})

        try:
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=MAX_TOKENS,
                system=system or anthropic.NOT_GIVEN,
                thinking={"type": "adaptive"},
                messages=messages,
            )
        except anthropic.AuthenticationError:
            raise AIError("chave inválida")
        except anthropic.PermissionDeniedError:
            raise AIError("chave sem permissão ou sem créditos")
        except anthropic.RateLimitError:
            raise AIError("cota/limite de uso esgotado")
        except anthropic.BadRequestError as e:
            if "credit balance" in str(e.message).lower():
                raise AIError("sem créditos na conta Anthropic")
            raise AIError(f"requisição rejeitada: {redact(str(e.message)[:120])}")
        except anthropic.APIStatusError as e:
            raise AIError(f"erro da API Claude (HTTP {e.status_code})")
        except anthropic.APIConnectionError:
            raise AIError("falha de rede ao contatar a API Claude")

        if response.stop_reason == "refusal":
            raise AIError("o modelo recusou a solicitação")

        texto = "".join(b.text for b in response.content if b.type == "text")
        if not texto:
            raise AIError("o modelo não retornou texto")
        return texto

    def _call_gemini(self, key: str, prompt: str, system: str,
                     history: list[tuple[str, str]]) -> str:
        contents = []
        for role, text in (history or []):
            contents.append({
                "role": "user" if role == "user" else "model",
                "parts": [{"text": text}],
            })
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        body = {"contents": contents}
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}

        try:

            resp = requests.post(
                f"{GEMINI_BASE_URL}/{GEMINI_MODEL}:generateContent",
                headers={"x-goog-api-key": key},
                json=body,
                timeout=HTTP_TIMEOUT,
            )
        except requests.RequestException as e:
            raise AIError(f"falha de rede: {redact(e)}")

        if resp.status_code in (401, 403):
            raise AIError("chave inválida ou sem permissão")
        if resp.status_code == 429:
            raise AIError("cota de tokens esgotada")

        try:
            data = resp.json()
        except ValueError:
            raise AIError(f"resposta inesperada (HTTP {resp.status_code})")

        if "error" in data:
            raise AIError(redact(data["error"].get("message", "erro desconhecido")))

        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError):
            raise AIError("o modelo não retornou texto")
