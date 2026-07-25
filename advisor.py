import json
from datetime import datetime

from ai_client import AIClient, AIError
from pierre_client import PierreClient
from config import MONTHS_PT

SYSTEM_PROMPT = """Você é o Conselheiro do app "Na Ponta", um consultor financeiro pessoal brasileiro.
Você recebe os dados financeiros REAIS do usuário (transações, saldos, faturas, parcelas) e responde em português do Brasil.

Regras:
- Seja específico e use os números reais dos dados fornecidos (valores em R$).
- Dê planos de ação concretos e passo a passo, não conselhos genéricos.
- Para dívidas: compare estratégia avalanche (maior juro primeiro) vs bola de neve (menor saldo primeiro) quando fizer sentido.
- Para parcelamentos: analise se a parcela cabe no fluxo de caixa mensal real do usuário antes de recomendar.
- Para investimentos: priorize reserva de emergência (3-6 meses de despesas) antes de sugerir qualquer outro investimento; seja conservador.
- Quando recomendar investimentos específicos, lembre brevemente que você não substitui um assessor certificado.
- Formate com títulos curtos e listas quando ajudar a leitura. Evite tabelas.
- Se os dados fornecidos não forem suficientes para responder, diga o que falta em vez de inventar."""

def _pierre_safe(fn, default):
    try:
        return fn()
    except Exception as e:
        print(f"[Advisor] Pierre indisponível: {e}")
        return default

def build_financial_context(sync) -> str:
    now = datetime.now()
    partes = [f"Data de hoje: {now.strftime('%d/%m/%Y')}"]

    try:
        from technician import knowledge_summary
        conhecimento = knowledge_summary()
        if conhecimento:
            partes.append(
                "CONTEXTO DEFINIDO PELO USUÁRIO (via Técnico) — use para interpretar os dados:\n"
                + conhecimento
            )
    except Exception:
        pass

    resumo = sync.get_monthly_summary()
    partes.append(
        f"Mês atual ({MONTHS_PT[now.month - 1]}/{now.year}): "
        f"receitas R$ {resumo['receitas']:.2f}, despesas R$ {resumo['despesas']:.2f}, "
        f"saldo R$ {resumo['saldo']:.2f}"
    )

    meses = sync.get_last_n_months_summary(6)
    linhas = [
        f"  {m['mes_full']}/{m['ano']}: receitas R$ {m['receitas']:.2f}, "
        f"despesas R$ {m['despesas']:.2f}, saldo R$ {m['saldo']:.2f}"
        for m in meses
    ]
    partes.append("Últimos 6 meses:\n" + "\n".join(linhas))

    gastos = sync.get_expenses_by_category()
    if gastos:
        ordenado = sorted(gastos.items(), key=lambda x: x[1], reverse=True)
        linhas = [f"  {cat}: R$ {val:.2f}" for cat, val in ordenado]
        partes.append("Despesas do mês por categoria:\n" + "\n".join(linhas))

    client = PierreClient()
    if client.is_configured:
        saldo = _pierre_safe(client.get_balance, {})
        if saldo:
            contas = [
                f"  {a.get('name', 'Conta')}: R$ {float(a.get('balance') or 0):.2f}"
                for a in (saldo.get("accounts") or [])
            ]
            partes.append(
                f"Saldos bancários reais (Open Finance): total R$ {float(saldo.get('total_balance') or 0):.2f}\n"
                + "\n".join(contas)
            )

        fatura = _pierre_safe(lambda: client._get("get-bill-summary").get("data", {}), {})
        if fatura:
            partes.append(
                f"Fatura atual do(s) cartão(ões): R$ {float(fatura.get('totalAmount') or 0):.2f} "
                f"({fatura.get('totalTransactions', 0)} lançamentos)"
            )

        parcelas = _pierre_safe(lambda: client._get("get-installments").get("data", {}), {})
        if parcelas.get("summary"):
            partes.append(
                "Parcelamentos em aberto (resumo JSON): "
                + json.dumps(parcelas["summary"], ensure_ascii=False, default=str)[:1500]
            )
        compras = parcelas.get("purchases") or []
        if compras:
            linhas = []
            for p in compras[:12]:
                linhas.append("  " + json.dumps(p, ensure_ascii=False, default=str)[:220])
            partes.append("Compras parceladas (JSON, até 12):\n" + "\n".join(linhas))

    return "\n\n".join(partes)

def ask_advisor(sync, question: str, history: list[tuple[str, str]] = None) -> dict:
    client = AIClient()
    contexto = build_financial_context(sync)

    prompt = (
        f"DADOS FINANCEIROS ATUAIS DO USUÁRIO:\n{contexto}\n\n"
        f"PERGUNTA DO USUÁRIO:\n{question}"
    )

    texto = client.generate(prompt, system=SYSTEM_PROMPT, history=history,
                            prefer_provider="anthropic")
    return {"texto": texto, "chave_usada": client.last_key_used}

def monthly_diagnosis(sync) -> dict:
    return ask_advisor(
        sync,
        "Faça um diagnóstico completo da minha saúde financeira: "
        "1) Como está este mês (receitas vs despesas, onde estou gastando demais); "
        "2) Situação de dívidas, fatura de cartão e parcelamentos — e a melhor estratégia para quitá-los; "
        "3) Quanto sobra de verdade e qual seria meu plano de investimento ideal começando agora "
        "(reserva de emergência primeiro, depois o resto). "
        "Termine com as 3 ações mais importantes para eu fazer esta semana.",
    )
