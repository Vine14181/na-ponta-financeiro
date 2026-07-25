import json
from datetime import date, timedelta

from ai_client import AIClient
from pierre_client import PierreClient

SYSTEM_PROMPT = """Você é o Pierre, um assistente de finanças pessoais brasileiro criado para conversar com o dinheiro do usuário.
Seu jeito: calmo, direto e acolhedor. Você fala em português do Brasil, em linguagem natural — nada de planilhas, tabelas ou jargão financeiro. Você traduz os números em frases simples e tranquilizadoras, como um amigo competente que está de olho nas finanças da pessoa.

Você recebe os dados financeiros REAIS do usuário (contas, saldos, transações, faturas de cartão, parcelas) vindos do Open Finance. Use-os para responder com precisão, sempre citando valores em reais quando fizer sentido.

Regras:
- Respostas curtas e conversadas. Evite listas longas; prefira 1 a 3 frases quando possível.
- Nunca invente dados. Se não estiver nos dados fornecidos, diga que não tem essa informação conectada.
- Seja gentil e prático. Se algo merece atenção (fatura alta, saldo baixo), avise com leveza.
- Não use markdown pesado (sem #, sem **). Texto corrido e humano."""

def _safe(fn, default):
    try:
        return fn()
    except Exception as e:
        print(f"[Pierre] indisponível: {e}")
        return default

def build_pierre_context() -> str:
    client = PierreClient()
    if not client.is_configured:
        return ""

    partes = [f"Data de hoje: {date.today().strftime('%d/%m/%Y')}"]

    saldo = _safe(client.get_balance, {})
    if saldo:
        contas = [
            f"  - {a.get('name', 'Conta')}: R$ {float(a.get('balance') or 0):.2f}"
            for a in (saldo.get("accounts") or [])
        ]
        partes.append(
            f"Saldo total: R$ {float(saldo.get('total_balance') or 0):.2f}\nContas:\n"
            + "\n".join(contas)
        )

    fatura = _safe(lambda: client._get("get-bill-summary").get("data", {}), {})
    if fatura:
        partes.append(
            f"Fatura atual do cartão: R$ {float(fatura.get('totalAmount') or 0):.2f} "
            f"({fatura.get('totalTransactions', 0)} lançamentos)"
        )

    parcelas = _safe(lambda: client._get("get-installments").get("data", {}), {})
    if parcelas.get("summary"):
        partes.append(
            "Resumo de parcelamentos (JSON): "
            + json.dumps(parcelas["summary"], ensure_ascii=False, default=str)[:1200]
        )

    end = date.today()
    start = end - timedelta(days=30)
    txs = _safe(lambda: client.get_transactions(start.isoformat(), end.isoformat()), [])
    if txs:
        linhas = []
        for t in txs[:40]:
            tipo = "entrou" if str(t.get("type", "")).upper() == "CREDIT" else "saiu"
            linhas.append(
                f"  - {str(t.get('date', ''))[:10]}: {tipo} R$ {abs(float(t.get('amount') or 0)):.2f}"
                f" — {(t.get('description') or '')[:50]} [{t.get('category', '')}]"
            )
        partes.append(f"Transações dos últimos 30 dias ({len(txs)} no total, mostrando até 40):\n" + "\n".join(linhas))

    return "\n\n".join(partes)

def ask_pierre(question: str, history: list[tuple[str, str]] = None) -> dict:
    client = AIClient()
    contexto = build_pierre_context()
    if not contexto:
        return {
            "texto": "Ainda não tenho seus dados do Pierre conectados. "
                     "Confira a chave do Pierre em Configurações → Cofre de API Keys.",
            "chave_usada": "",
        }

    prompt = f"DADOS FINANCEIROS REAIS DO USUÁRIO (Open Finance):\n{contexto}\n\nPERGUNTA:\n{question}"

    texto = client.generate(prompt, system=SYSTEM_PROMPT, history=history,
                            prefer_provider="gemini")
    return {"texto": texto, "chave_usada": client.last_key_used}
