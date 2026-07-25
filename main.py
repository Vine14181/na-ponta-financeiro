import sys
import os

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, APP_DIR)

import netguard
netguard.activate()

from sheets_sync import SheetsSync

def main():
    print("=" * 50)
    print("  💰 Na Ponta — Controle Financeiro")
    print("=" * 50)
    print()

    sync = SheetsSync()

    print("[*] Conectando ao Google Sheets...")
    connected = sync.connect()
    if connected:
        print(f"[✓] Conectado com sucesso! (método: {sync.backend})")
        print("[*] Carregando dados da planilha...")
        df = sync.pull_data()
        print(f"[✓] {len(df)} transações carregadas.")
    else:
        print("[!] Sem conexão configurada. O app iniciará em modo offline.")
        print("    Para sincronizar (gratuito): siga as instruções em apps_script.gs")
        print("    e cole a URL nas Configurações do app.")

    print()
    print("[*] Iniciando interface gráfica...")
    print()

    from app import NaPontaApp
    app = NaPontaApp(sync)
    app.mainloop()

if __name__ == "__main__":
    main()
