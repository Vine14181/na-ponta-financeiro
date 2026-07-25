import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))

_LOCAL_BASE = (
    os.environ.get("LOCALAPPDATA")
    or os.environ.get("APPDATA")
    or os.path.join(os.path.expanduser("~"), ".local", "share")
)
DATA_DIR = os.path.join(_LOCAL_BASE, "NaPonta")
_LEGACY_DATA_DIR = os.path.join(APP_DIR, "data")

CREDENTIALS_PATH = os.path.join(APP_DIR, "credentials.json")
KEYS_FILE = os.path.join(DATA_DIR, "api_keys.enc")
MASTER_KEY_FILE = os.path.join(DATA_DIR, ".master.key")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

os.makedirs(DATA_DIR, exist_ok=True)

def _migrate_legacy_data():
    import shutil
    if not os.path.isdir(_LEGACY_DATA_DIR):
        return
    arquivos = ["api_keys.enc", ".master.key", "settings.json", "knowledge.json"]
    migrou = False
    for nome in arquivos:
        origem = os.path.join(_LEGACY_DATA_DIR, nome)
        destino = os.path.join(DATA_DIR, nome)
        if os.path.exists(origem) and not os.path.exists(destino):
            try:
                shutil.copy2(origem, destino)
                migrou = True
            except Exception as e:
                print(f"[config] Falha ao migrar {nome}: {e}")
    if migrou:
        aviso = os.path.join(_LEGACY_DATA_DIR, "LEIA_MOVA_ESTA_PASTA.txt")
        try:
            with open(aviso, "w", encoding="utf-8") as f:
                f.write(
                    "Os segredos do Na Ponta foram movidos para uma pasta LOCAL "
                    "(fora do Google Drive), por segurança:\n"
                    f"  {DATA_DIR}\n\n"
                    "Você pode APAGAR esta pasta 'data/' com segurança — ela está "
                    "dentro do Google Drive e não deve guardar chaves nem a chave-mestra.\n"
                )
        except Exception:
            pass

_migrate_legacy_data()

ENV_FILE = os.path.join(APP_DIR, ".env")

def _load_dotenv():
    try:
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha or linha.startswith("#") or "=" not in linha:
                    continue
                chave, _, valor = linha.partition("=")
                chave = chave.strip()
                valor = valor.strip().strip('"').strip("'")
                if chave and chave not in os.environ:
                    os.environ[chave] = valor
    except FileNotFoundError:
        pass

_load_dotenv()

_ENV_TO_SETTING = {
    "NAPONTA_APPS_SCRIPT_URL": "apps_script_url",
    "NAPONTA_APPS_SCRIPT_TOKEN": "apps_script_token",
}

def load_settings() -> dict:
    import json
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        settings = {}

    for env_key, setting_key in _ENV_TO_SETTING.items():
        valor = os.environ.get(env_key)
        if valor:
            settings[setting_key] = valor

    return settings

def save_settings(settings: dict):
    import json
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

def update_setting(key: str, value):
    settings = load_settings()
    settings[key] = value
    save_settings(settings)

SPREADSHEET_NAME = "Financeiro"
SHEET_TRANSACTIONS = "Transações"
SHEET_CATEGORIES = "Categorias"
SHEET_SUMMARY = "Resumo Mensal"
SHEET_GOALS = "Metas"

TRANSACTION_HEADERS = [
    "ID", "Data", "Tipo", "Categoria", "Subcategoria",
    "Descrição", "Valor", "Método Pagamento", "Status",
    "Observações", "Mês", "Ano", "Atualizado"
]

EXPENSE_CATEGORIES = {
    "🏠 Moradia": ["Aluguel", "Condomínio", "IPTU", "Manutenção"],
    "🍽️ Alimentação": ["Supermercado", "Restaurantes", "Delivery", "Lanches"],
    "🚗 Transporte": ["Combustível", "Uber/Táxi", "Estacionamento", "Manutenção Veículo", "Transporte Público"],
    "💊 Saúde": ["Plano de Saúde", "Farmácia", "Consultas", "Academia"],
    "📚 Educação": ["Mensalidade", "Livros", "Cursos"],
    "👕 Vestuário": ["Roupas", "Calçados", "Acessórios"],
    "🎮 Lazer": ["Streaming", "Jogos", "Viagens", "Hobbies"],
    "💡 Contas": ["Luz", "Água", "Gás", "Internet", "Telefone"],
    "🐕 Pets": ["Ração", "Veterinário", "Petshop"],
    "💇 Pessoal": ["Cabeleireiro", "Cosméticos", "Cuidados"],
    "📦 Compras": ["Eletrônicos", "Casa", "Presentes"],
    "💳 Financeiro": ["Juros", "Multas", "Taxas Bancárias", "Seguros"],
    "📌 Outros": ["Outros"],
}

INCOME_CATEGORIES = {
    "💰 Salário": ["Salário Principal", "13º", "Férias"],
    "💼 Freelance": ["Projetos", "Consultoria"],
    "📈 Investimentos": ["Dividendos", "Rendimentos", "Juros"],
    "🎁 Presentes": ["Bonificações", "Presentes"],
    "💵 Vendas": ["Vendas"],
    "📌 Outras Receitas": ["Outras"],
}

PAYMENT_METHODS = [
    "Pix", "Cartão Crédito", "Cartão Débito",
    "Dinheiro", "Boleto", "Transferência"
]

TRANSACTION_STATUS = ["Pago", "Pendente", "Atrasado"]

CURRENCIES = {
    "BRL": {"symbol": "R$", "locale": "pt_BR"},
    "USD": {"symbol": "$", "locale": "en_US"},
    "EUR": {"symbol": "€", "locale": "de_DE"},
}
DEFAULT_CURRENCY = "BRL"

MONTHS_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril",
    "Maio", "Junho", "Julho", "Agosto",
    "Setembro", "Outubro", "Novembro", "Dezembro"
]
