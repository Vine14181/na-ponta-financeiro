import json
import re
from datetime import datetime

from ai_client import AIClient
from config import (
    DATA_DIR, EXPENSE_CATEGORIES, INCOME_CATEGORIES,
)
import os

KNOWLEDGE_FILE = os.path.join(DATA_DIR, "knowledge.json")

SYSTEM_PROMPT = """Você é o TÉCNICO do app "Na Ponta" — arquiteto de dados e controlador de informações financeiras do usuário.
Sua função: receber instruções do usuário sobre como classificar e interpretar os dados financeiros dele, e transformá-las em regras estruturadas que o aplicativo aplica automaticamente.

Você responde SEMPRE e SOMENTE com um JSON válido neste formato (sem texto fora do JSON, sem markdown):
{
  "resposta": "sua resposta em português para o usuário, curta e clara",
  "acoes": [ ...zero ou mais ações... ]
}

Tipos de ação disponíveis:

1. Regra de categorização — quando o usuário disser que um gasto/estabelecimento pertence a uma categoria ou finalidade:
{"tipo": "regra", "corresponde": "texto a procurar na descrição da transação", "categoria": "<categoria do app>", "subcategoria": "<opcional>", "finalidade": "<opcional: casa, investimento, trabalho, etc>"}

2. Recorrência — quando o usuário descrever algo que acontece repetidamente (PIX mensal, conta fixa, aporte):
{"tipo": "recorrencia", "descricao": "o que é", "valor": 0.0, "frequencia": "mensal|semanal|anual|dias:N", "finalidade": "<para que serve>", "categoria": "<categoria do app, opcional>"}

3. Fato de perfil — informação sobre o usuário/contexto que não é regra nem recorrência:
{"tipo": "fato", "texto": "o fato em uma frase"}

4. Remover — quando o usuário pedir para apagar algo que ensinou antes:
{"tipo": "remover", "alvo": "regra|recorrencia|fato", "corresponde": "trecho que identifica o item"}

Categorias válidas de DESPESA: {EXPENSE_CATS}
Categorias válidas de RECEITA: {INCOME_CATS}

Regras de comportamento:
- Use exatamente os nomes de categoria válidos acima (com o emoji).
- "corresponde" deve ser um trecho curto e distintivo da descrição real da transação (ex.: nome do estabelecimento).
- Se o usuário só fizer uma pergunta ou comentário, responda em "resposta" e retorne "acoes": [].
- Se a instrução for ambígua, pergunte em "resposta" antes de criar a ação.
- Confirme em "resposta" o que você registrou, de forma natural."""

def load_knowledge() -> dict:
    try:
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    data.setdefault("regras", [])
    data.setdefault("recorrencias", [])
    data.setdefault("fatos", [])
    return data

def save_knowledge(data: dict):
    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def knowledge_summary() -> str:
    k = load_knowledge()
    partes = []
    if k["regras"]:
        linhas = [
            f"  - transações contendo '{r['corresponde']}' são {r.get('categoria', '?')}"
            + (f" / {r['subcategoria']}" if r.get("subcategoria") else "")
            + (f" (finalidade: {r['finalidade']})" if r.get("finalidade") else "")
            for r in k["regras"]
        ]
        partes.append("Regras de classificação definidas pelo usuário:\n" + "\n".join(linhas))
    if k["recorrencias"]:
        linhas = [
            f"  - {r['descricao']}: R$ {float(r.get('valor') or 0):.2f}, {r.get('frequencia', '?')}"
            + (f", finalidade: {r['finalidade']}" if r.get("finalidade") else "")
            for r in k["recorrencias"]
        ]
        partes.append("Movimentações recorrentes conhecidas:\n" + "\n".join(linhas))
    if k["fatos"]:
        partes.append("Fatos sobre o usuário:\n" + "\n".join(f"  - {f}" for f in k["fatos"]))
    return "\n\n".join(partes)

def apply_rule_to_row(row: dict) -> dict:
    regras = load_knowledge()["regras"]
    descricao = str(row.get("Descrição", "")).lower()
    for regra in regras:
        if regra["corresponde"].lower() in descricao:
            if regra.get("categoria"):
                row["Categoria"] = regra["categoria"]
            if regra.get("subcategoria"):
                row["Subcategoria"] = regra["subcategoria"]
            if regra.get("finalidade"):
                obs = str(row.get("Observações", ""))
                marca = f"Fim: {regra['finalidade']}"
                if marca not in obs:
                    row["Observações"] = (obs + " | " if obs else "") + marca
            break
    return row

def apply_rules_to_existing(sync, regras: list[dict] = None) -> int:
    regras = regras if regras is not None else load_knowledge()["regras"]
    df = sync.dataframe
    if df.empty or not regras:
        return 0

    alteradas = 0
    for idx in df.index:
        descricao = str(df.at[idx, "Descrição"]).lower()
        for regra in regras:
            if regra["corresponde"].lower() not in descricao:
                continue
            mudou = False
            if regra.get("categoria") and df.at[idx, "Categoria"] != regra["categoria"]:
                df.at[idx, "Categoria"] = regra["categoria"]
                mudou = True
            if regra.get("subcategoria") and df.at[idx, "Subcategoria"] != regra["subcategoria"]:
                df.at[idx, "Subcategoria"] = regra["subcategoria"]
                mudou = True
            if regra.get("finalidade"):
                obs = str(df.at[idx, "Observações"] or "")
                marca = f"Fim: {regra['finalidade']}"
                if marca not in obs:
                    df.at[idx, "Observações"] = (obs + " | " if obs else "") + marca
                    mudou = True
            if mudou:
                df.at[idx, "Atualizado"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                alteradas += 1
            break
    if alteradas:
        sync._sync_full_async()
    return alteradas

def _parse_json_response(texto: str) -> dict:
    texto = texto.strip()
    texto = re.sub(r"^```(?:json)?\s*", "", texto)
    texto = re.sub(r"\s*```$", "", texto)
    inicio = texto.find("{")
    fim = texto.rfind("}")
    if inicio == -1 or fim == -1:
        raise ValueError("resposta sem JSON")
    return json.loads(texto[inicio:fim + 1])

def _categorias_validas() -> set:
    return set(EXPENSE_CATEGORIES.keys()) | set(INCOME_CATEGORIES.keys())

def _texto_seguro(valor, max_len: int = 80) -> str:
    s = str(valor or "").strip()
    while s and s[0] in ("=", "+", "-", "@"):
        s = s[1:].strip()
    return s[:max_len]

def _apply_actions(sync, acoes: list[dict]) -> list[str]:
    k = load_knowledge()
    feitos = []
    regras_novas = []
    validas = _categorias_validas()

    for acao in acoes or []:
        tipo = acao.get("tipo")
        if tipo == "regra" and acao.get("corresponde"):
            corresponde = _texto_seguro(acao.get("corresponde"), 60)
            if len(corresponde) < 3:
                feitos.append("regra ignorada (trecho muito curto/genérico)")
                continue
            categoria = str(acao.get("categoria") or "").strip()
            if categoria and categoria not in validas:
                feitos.append(f"regra ignorada (categoria inválida: {_texto_seguro(categoria, 30)})")
                continue
            regra = {"corresponde": corresponde}
            if categoria:
                regra["categoria"] = categoria
            if acao.get("subcategoria"):
                regra["subcategoria"] = _texto_seguro(acao["subcategoria"], 40)
            if acao.get("finalidade"):
                regra["finalidade"] = _texto_seguro(acao["finalidade"], 40)
            regra["criada_em"] = datetime.now().strftime("%d/%m/%Y")
            k["regras"] = [r for r in k["regras"] if r["corresponde"].lower() != corresponde.lower()]
            k["regras"].append(regra)
            regras_novas.append(regra)
            feitos.append(f"regra: '{corresponde}' → {regra.get('categoria', '(sem categoria)')}")
        elif tipo == "recorrencia" and acao.get("descricao"):
            categoria = str(acao.get("categoria") or "").strip()
            if categoria and categoria not in validas:
                acao = dict(acao)
                acao.pop("categoria", None)
            rec = {c: acao[c] for c in ("descricao", "valor", "frequencia", "finalidade", "categoria") if acao.get(c) is not None}
            rec["criada_em"] = datetime.now().strftime("%d/%m/%Y")
            k["recorrencias"] = [r for r in k["recorrencias"] if r["descricao"].lower() != rec["descricao"].lower()]
            k["recorrencias"].append(rec)
            feitos.append(f"recorrência: {rec['descricao']}")
        elif tipo == "fato" and acao.get("texto"):
            if acao["texto"] not in k["fatos"]:
                k["fatos"].append(acao["texto"])
            feitos.append("fato registrado")
        elif tipo == "remover" and acao.get("corresponde"):
            alvo = acao.get("alvo", "")
            trecho = acao["corresponde"].lower()
            if alvo == "regra":
                antes = len(k["regras"])
                k["regras"] = [r for r in k["regras"] if trecho not in r["corresponde"].lower()]
                feitos.append(f"{antes - len(k['regras'])} regra(s) removida(s)")
            elif alvo == "recorrencia":
                antes = len(k["recorrencias"])
                k["recorrencias"] = [r for r in k["recorrencias"] if trecho not in r["descricao"].lower()]
                feitos.append(f"{antes - len(k['recorrencias'])} recorrência(s) removida(s)")
            elif alvo == "fato":
                antes = len(k["fatos"])
                k["fatos"] = [f for f in k["fatos"] if trecho not in f.lower()]
                feitos.append(f"{antes - len(k['fatos'])} fato(s) removido(s)")

    save_knowledge(k)

    if regras_novas:
        alteradas = apply_rules_to_existing(sync, regras_novas)
        if alteradas:
            feitos.append(f"{alteradas} transações existentes recategorizadas")

    return feitos

def ask_technician(sync, question: str, history: list[tuple[str, str]] = None) -> dict:
    client = AIClient()

    system = SYSTEM_PROMPT.replace(
        "{EXPENSE_CATS}", ", ".join(EXPENSE_CATEGORIES.keys())
    ).replace(
        "{INCOME_CATS}", ", ".join(INCOME_CATEGORIES.keys())
    )

    conhecimento = knowledge_summary()
    prompt = ""
    if conhecimento:
        prompt += f"CONHECIMENTO JÁ REGISTRADO:\n{conhecimento}\n\n"
    prompt += f"MENSAGEM DO USUÁRIO:\n{question}"

    bruto = client.generate(prompt, system=system, history=history, prefer_provider="anthropic")

    try:
        dados = _parse_json_response(bruto)
    except (ValueError, json.JSONDecodeError):

        return {"texto": bruto.strip(), "chave_usada": client.last_key_used, "acoes_feitas": []}

    acoes_feitas = _apply_actions(sync, dados.get("acoes", []))
    return {
        "texto": dados.get("resposta", "").strip() or "Registrado.",
        "chave_usada": client.last_key_used,
        "acoes_feitas": acoes_feitas,
    }
