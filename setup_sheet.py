import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    CREDENTIALS_PATH, SPREADSHEET_NAME,
    SHEET_TRANSACTIONS, SHEET_CATEGORIES, SHEET_SUMMARY, SHEET_GOALS,
    TRANSACTION_HEADERS, EXPENSE_CATEGORIES, INCOME_CATEGORIES,
    PAYMENT_METHODS, TRANSACTION_STATUS, MONTHS_PT,
)

def setup_spreadsheet():
    import gspread

    print("=" * 50)
    print("  📊 Na Ponta — Configuração da Planilha")
    print("=" * 50)

    if not os.path.exists(CREDENTIALS_PATH):
        print(f"\n[ERRO] Arquivo credentials.json não encontrado em:\n  {CREDENTIALS_PATH}")
        print("\nPor favor, siga o README.md para configurar as credenciais.")
        return False

    gc = gspread.service_account(filename=CREDENTIALS_PATH)

    try:
        spreadsheet = gc.open(SPREADSHEET_NAME)
        print(f"\n[✓] Planilha '{SPREADSHEET_NAME}' encontrada!")
    except gspread.SpreadsheetNotFound:
        print(f"\n[!] Planilha '{SPREADSHEET_NAME}' não encontrada.")
        print("    Certifique-se de compartilhá-la com o email da Service Account.")
        return False

    print(f"\n[*] Configurando aba '{SHEET_TRANSACTIONS}'...")
    try:
        ws_tx = spreadsheet.worksheet(SHEET_TRANSACTIONS)
        print(f"    Aba existente encontrada.")
    except gspread.WorksheetNotFound:
        ws_tx = spreadsheet.add_worksheet(
            title=SHEET_TRANSACTIONS, rows=1000, cols=len(TRANSACTION_HEADERS)
        )
        print(f"    Aba criada!")

    ws_tx.update("A1", [TRANSACTION_HEADERS])

    ws_tx.format("A1:M1", {
        "backgroundColor": {"red": 0.05, "green": 0.07, "blue": 0.13},
        "textFormat": {"bold": True, "foregroundColor": {"red": 0.94, "green": 0.96, "blue": 0.99}},
        "horizontalAlignment": "CENTER",
    })
    print(f"    Headers configurados.")

    print(f"\n[*] Configurando aba '{SHEET_CATEGORIES}'...")
    try:
        ws_cat = spreadsheet.worksheet(SHEET_CATEGORIES)
    except gspread.WorksheetNotFound:
        ws_cat = spreadsheet.add_worksheet(title=SHEET_CATEGORIES, rows=100, cols=4)

    ws_cat.clear()
    ws_cat.update("A1", [["CATEGORIAS DE DESPESA", "Subcategorias", "", "CATEGORIAS DE RECEITA"]])

    row = 2
    for cat, subcats in EXPENSE_CATEGORIES.items():
        ws_cat.update(f"A{row}", [[cat, ", ".join(subcats)]])
        row += 1

    row_income = 2
    for cat, subcats in INCOME_CATEGORIES.items():
        ws_cat.update(f"D{row_income}", [[cat, ", ".join(subcats)]])
        row_income += 1

    ws_cat.update(f"A{row + 1}", [["MÉTODOS DE PAGAMENTO"]])
    for i, method in enumerate(PAYMENT_METHODS):
        ws_cat.update(f"A{row + 2 + i}", [[method]])

    ws_cat.update(f"D{row_income + 1}", [["STATUS"]])
    for i, status in enumerate(TRANSACTION_STATUS):
        ws_cat.update(f"D{row_income + 2 + i}", [[status]])

    print(f"    Categorias configuradas.")

    print(f"\n[*] Configurando aba '{SHEET_SUMMARY}'...")
    try:
        ws_sum = spreadsheet.worksheet(SHEET_SUMMARY)
    except gspread.WorksheetNotFound:
        ws_sum = spreadsheet.add_worksheet(title=SHEET_SUMMARY, rows=50, cols=6)

    ws_sum.clear()
    ws_sum.update("A1", [["Mês", "Ano", "Receitas", "Despesas", "Saldo", "% Economia"]])

    import datetime
    year = datetime.datetime.now().year

    for i, month in enumerate(MONTHS_PT):
        row_num = i + 2
        ws_sum.update(f"A{row_num}", [[month]])
        ws_sum.update(f"B{row_num}", [[str(year)]])

        ws_sum.update(f"C{row_num}", [[
            f'=SUMIFS(\'{SHEET_TRANSACTIONS}\'!G:G,\'{SHEET_TRANSACTIONS}\'!C:C,"Receita",\'{SHEET_TRANSACTIONS}\'!K:K,A{row_num},\'{SHEET_TRANSACTIONS}\'!L:L,B{row_num})'
        ]])
        ws_sum.update(f"D{row_num}", [[
            f'=SUMIFS(\'{SHEET_TRANSACTIONS}\'!G:G,\'{SHEET_TRANSACTIONS}\'!C:C,"Despesa",\'{SHEET_TRANSACTIONS}\'!K:K,A{row_num},\'{SHEET_TRANSACTIONS}\'!L:L,B{row_num})'
        ]])
        ws_sum.update(f"E{row_num}", [[f"=C{row_num}-D{row_num}"]])
        ws_sum.update(f"F{row_num}", [[f'=IF(C{row_num}>0,(C{row_num}-D{row_num})/C{row_num}*100,0)']])

    ws_sum.format("A1:F1", {
        "backgroundColor": {"red": 0.05, "green": 0.07, "blue": 0.13},
        "textFormat": {"bold": True, "foregroundColor": {"red": 0.94, "green": 0.96, "blue": 0.99}},
        "horizontalAlignment": "CENTER",
    })
    print(f"    Resumo mensal com fórmulas configurado.")

    print(f"\n[*] Configurando aba '{SHEET_GOALS}'...")
    try:
        ws_goals = spreadsheet.worksheet(SHEET_GOALS)
    except gspread.WorksheetNotFound:
        ws_goals = spreadsheet.add_worksheet(title=SHEET_GOALS, rows=20, cols=5)

    ws_goals.clear()
    ws_goals.update("A1", [["Meta", "Valor Alvo", "Valor Atual", "Prazo", "% Conclusão"]])

    ws_goals.update("A2", [["Reserva de Emergência", "10000", "0", "31/12/2026", "=C2/B2*100"]])

    ws_goals.format("A1:E1", {
        "backgroundColor": {"red": 0.05, "green": 0.07, "blue": 0.13},
        "textFormat": {"bold": True, "foregroundColor": {"red": 0.94, "green": 0.96, "blue": 0.99}},
        "horizontalAlignment": "CENTER",
    })
    print(f"    Metas configuradas.")

    print("\n" + "=" * 50)
    print("  ✅ Planilha configurada com sucesso!")
    print("=" * 50)
    print(f"\n  Abas criadas:")
    print(f"    📝 {SHEET_TRANSACTIONS} — Dados das transações")
    print(f"    📂 {SHEET_CATEGORIES} — Categorias e subcategorias")
    print(f"    📊 {SHEET_SUMMARY} — Resumo mensal automático")
    print(f"    🎯 {SHEET_GOALS} — Metas financeiras")
    print(f"\n  Agora execute: python main.py")

    return True

if __name__ == "__main__":
    setup_spreadsheet()
