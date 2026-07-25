from datetime import datetime, date, timedelta

import requests

from key_vault import KeyVault
from config import MONTHS_PT

BASE_URL = "https://www.pierre.finance/tools/api"
HTTP_TIMEOUT = 90

class PierreClient:

    def __init__(self, api_key: str = None):
        self._api_key = api_key

    @property
    def api_key(self) -> str:
        if self._api_key is None:
            self._api_key = KeyVault().get_key("pierre") or ""
        return self._api_key

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _get(self, endpoint: str, params: dict = None) -> dict:
        resp = requests.get(
            f"{BASE_URL}/{endpoint}",
            headers={"Authorization": f"Bearer {self.api_key}"},
            params=params or {},
            timeout=HTTP_TIMEOUT,
        )
        try:
            data = resp.json()
        except ValueError:
            raise RuntimeError(f"Pierre API: resposta inesperada (HTTP {resp.status_code})")
        if not isinstance(data, dict):
            raise RuntimeError("Pierre API: formato de resposta inesperado")
        if not data.get("success"):
            erro = data.get("error") or data.get("message") or f"HTTP {resp.status_code}"
            raise RuntimeError(f"Pierre API: {erro}")
        return data

    def get_accounts(self) -> list[dict]:
        return self._get("get-accounts").get("data", [])

    def get_balance(self) -> dict:
        return self._get("get-balance").get("data", {})

    def get_transactions(self, start_date: str = None, end_date: str = None) -> list[dict]:
        params = {}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        return self._get("get-transactions", params).get("data", [])

SKIP_CATEGORIES = {
    "Transferência mesma titularidade",
    "Pagamento de cartão de crédito",
}

EXPENSE_MAP = {
    "Supermercado": ("🍽️ Alimentação", "Supermercado"),
    "Restaurantes, bares e lanchonetes": ("🍽️ Alimentação", "Restaurantes"),
    "Delivery de comida": ("🍽️ Alimentação", "Delivery"),
    "Eletricidade": ("💡 Contas", "Luz"),
    "Gás": ("💡 Contas", "Gás"),
    "Água": ("💡 Contas", "Água"),
    "Internet": ("💡 Contas", "Internet"),
    "Telefonia": ("💡 Contas", "Telefone"),
    "Moradia": ("🏠 Moradia", ""),
    "Aluguel": ("🏠 Moradia", "Aluguel"),
    "Condomínio": ("🏠 Moradia", "Condomínio"),
    "Táxi e transporte privado urbano": ("🚗 Transporte", "Uber/Táxi"),
    "Transporte público": ("🚗 Transporte", "Transporte Público"),
    "Combustível": ("🚗 Transporte", "Combustível"),
    "Estacionamento": ("🚗 Transporte", "Estacionamento"),
    "Universidade": ("📚 Educação", "Mensalidade"),
    "Educação": ("📚 Educação", ""),
    "Cursos": ("📚 Educação", "Cursos"),
    "Compras": ("📦 Compras", ""),
    "Eletrônicos": ("📦 Compras", "Eletrônicos"),
    "Vestuário": ("👕 Vestuário", "Roupas"),
    "Saúde": ("💊 Saúde", ""),
    "Farmácia": ("💊 Saúde", "Farmácia"),
    "Academia": ("💊 Saúde", "Academia"),
    "Streaming": ("🎮 Lazer", "Streaming"),
    "Lazer": ("🎮 Lazer", ""),
    "Viagens": ("🎮 Lazer", "Viagens"),
    "Pets": ("🐕 Pets", ""),
    "Serviços": ("📌 Outros", "Serviços"),
    "Transferência - PIX": ("💳 Financeiro", "Pix"),
    "Transferências": ("💳 Financeiro", "Transferência"),
    "Juros": ("💳 Financeiro", "Juros"),
    "Taxas bancárias": ("💳 Financeiro", "Taxas Bancárias"),
    "Seguros": ("💳 Financeiro", "Seguros"),
}

INCOME_MAP = {
    "Salário": ("💰 Salário", "Salário Principal"),
    "Cashback": ("📌 Outras Receitas", "Outras"),
    "Rendimentos": ("📈 Investimentos", "Rendimentos"),
    "Dividendos": ("📈 Investimentos", "Dividendos"),
}

def _parse_date(raw: str) -> datetime:
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).replace(tzinfo=None)
    except (ValueError, TypeError):
        pass
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(raw)[:10], fmt)
        except ValueError:
            continue
    return datetime.now()

def _map_transaction(tx: dict) -> dict:
    is_income = str(tx.get("type", "")).upper() == "CREDIT"
    categoria_pierre = tx.get("category") or ""

    if is_income:
        categoria, sub = INCOME_MAP.get(categoria_pierre, ("📌 Outras Receitas", "Outras"))
    else:
        categoria, sub = EXPENSE_MAP.get(categoria_pierre, ("📌 Outros", "Outros"))

    dt = _parse_date(tx.get("date"))
    try:
        valor = abs(float(tx.get("amount") or 0))
    except (ValueError, TypeError):
        valor = 0.0

    conta_tipo = str(tx.get("account_type") or "").upper()
    metodo = "Cartão Crédito" if "CREDIT" in conta_tipo else "Pix"

    banco = tx.get("item_bank_name") or tx.get("account_name") or ""
    obs_partes = [p for p in [f"Pierre: {categoria_pierre}" if categoria_pierre else "", banco] if p]

    return {
        "ID": f"P-{tx.get('id', '')}"[:44],
        "Data": dt.strftime("%d/%m/%Y"),
        "Tipo": "Receita" if is_income else "Despesa",
        "Categoria": categoria,
        "Subcategoria": sub,
        "Descrição": (tx.get("description") or tx.get("original_description") or "")[:120],
        "Valor": f"{valor:.2f}",
        "Método Pagamento": metodo,
        "Status": "Pago",
        "Observações": " | ".join(obs_partes),
        "Mês": MONTHS_PT[dt.month - 1],
        "Ano": str(dt.year),
        "Atualizado": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }

def import_from_pierre(sync, days: int = 30) -> dict:
    client = PierreClient()
    if not client.is_configured:
        raise RuntimeError("Chave de API do Pierre não configurada no cofre.")

    end = date.today()
    start = end - timedelta(days=days)
    transacoes = client.get_transactions(start.isoformat(), end.isoformat())

    df = sync.dataframe
    ids_existentes = set(df["ID"].astype(str)) if not df.empty else set()

    try:
        from technician import apply_rule_to_row
    except Exception:
        apply_rule_to_row = None

    novas, duplicadas, ignoradas, com_erro = [], 0, 0, 0
    for tx in transacoes:
        try:
            if (tx.get("category") or "") in SKIP_CATEGORIES:
                ignoradas += 1
                continue
            row = _map_transaction(tx)
            if apply_rule_to_row:
                row = apply_rule_to_row(row)
            if row["ID"] in ids_existentes:
                duplicadas += 1
                continue
            ids_existentes.add(row["ID"])
            novas.append(row)
        except Exception as e:
            com_erro += 1
            print(f"[Pierre] transação ignorada por erro de dados: {e}")

    if novas:
        sync.bulk_add(novas)

    return {
        "importadas": len(novas),
        "duplicadas": duplicadas,
        "ignoradas": ignoradas,
        "com_erro": com_erro,
        "total_pierre": len(transacoes),
    }
