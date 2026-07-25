import os
import uuid
import threading
from datetime import datetime
from typing import Optional, Callable

import pandas as pd
import requests

from secutil import redact
from config import (
    CREDENTIALS_PATH, SPREADSHEET_NAME, SHEET_TRANSACTIONS,
    TRANSACTION_HEADERS, MONTHS_PT, load_settings,
)

HTTP_TIMEOUT = 30

_FORMULA_PREFIXOS = ("=", "+", "-", "@")

def _sanitize_cell(valor) -> str:
    s = "" if valor is None else str(valor)
    if s and s[0] in _FORMULA_PREFIXOS:
        return "'" + s
    return s

def _sanitize_row(valores) -> list:
    return [_sanitize_cell(v) for v in valores]

class SheetsSync:

    def __init__(self, credentials_path: str = None):
        self._credentials_path = credentials_path or CREDENTIALS_PATH
        self._gc = None
        self._spreadsheet = None
        self._worksheet = None
        self._df: Optional[pd.DataFrame] = None
        self._connected = False
        self._backend = None
        self._as_url = None
        self._as_token = None
        self._lock = threading.Lock()

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def backend(self) -> Optional[str]:
        return self._backend

    @property
    def dataframe(self) -> pd.DataFrame:
        if self._df is None:
            self._df = pd.DataFrame(columns=TRANSACTION_HEADERS)
        return self._df

    def connect(self) -> bool:
        if self._connect_apps_script():
            return True
        return self._connect_gspread()

    def _connect_apps_script(self) -> bool:
        settings = load_settings()
        url = (settings.get("apps_script_url") or "").strip()
        token = (settings.get("apps_script_token") or "").strip()

        if not url or not token:
            return False

        try:
            resp = requests.get(
                url, params={"token": token}, timeout=HTTP_TIMEOUT
            )
            data = resp.json()
            if not data.get("ok"):
                print(f"[SheetsSync] Apps Script recusou: {data.get('error')}")
                return False

            self._as_url = url
            self._as_token = token
            self._backend = "apps_script"
            self._connected = True
            return True
        except Exception as e:
            print(f"[SheetsSync] Erro ao conectar via Apps Script: {redact(e)}")
            return False

    def _connect_gspread(self) -> bool:
        if not os.path.exists(self._credentials_path):
            return False
        try:
            import gspread
            self._gc = gspread.service_account(filename=self._credentials_path)
            self._spreadsheet = self._gc.open(SPREADSHEET_NAME)

            try:
                self._worksheet = self._spreadsheet.worksheet(SHEET_TRANSACTIONS)
            except gspread.WorksheetNotFound:

                self._worksheet = self._spreadsheet.add_worksheet(
                    title=SHEET_TRANSACTIONS, rows=1000, cols=len(TRANSACTION_HEADERS)
                )
                self._worksheet.update("A1", [TRANSACTION_HEADERS])

            self._backend = "gspread"
            self._connected = True
            return True
        except Exception as e:
            print(f"[SheetsSync] Erro ao conectar: {redact(e)}")
            self._connected = False
            return False

    def connect_async(self, callback: Callable[[bool], None] = None):
        def _worker():
            result = self.connect()
            if callback:
                callback(result)
        threading.Thread(target=_worker, daemon=True).start()

    def pull_data(self) -> pd.DataFrame:
        with self._lock:
            if not self._connected:
                return self.dataframe

            try:
                if self._backend == "apps_script":
                    records = self._as_get_records()
                elif self._worksheet is not None:
                    records = self._worksheet.get_all_records()
                else:
                    return self.dataframe

                if records:
                    self._df = pd.DataFrame(records)

                    for col in TRANSACTION_HEADERS:
                        if col not in self._df.columns:
                            self._df[col] = ""

                    if "Data" in self._df.columns and len(self._df) > 0:
                        self._df["Data"] = pd.to_datetime(
                            self._df["Data"], format="%d/%m/%Y", errors="coerce"
                        )
                else:
                    self._df = pd.DataFrame(columns=TRANSACTION_HEADERS)
            except Exception as e:
                print(f"[SheetsSync] Erro ao puxar dados: {redact(e)}")

            return self.dataframe

    def pull_async(self, callback: Callable[[pd.DataFrame], None] = None):
        def _worker():
            df = self.pull_data()
            if callback:
                callback(df)
        threading.Thread(target=_worker, daemon=True).start()

    def add_transaction(self, data: dict) -> str:
        tx_id = uuid.uuid4().hex[:8].upper()
        now = datetime.now()

        row = {
            "ID": tx_id,
            "Data": data.get("Data", now.strftime("%d/%m/%Y")),
            "Tipo": data.get("Tipo", "Despesa"),
            "Categoria": data.get("Categoria", ""),
            "Subcategoria": data.get("Subcategoria", ""),
            "Descrição": data.get("Descrição", ""),
            "Valor": data.get("Valor", "0"),
            "Método Pagamento": data.get("Método Pagamento", "Pix"),
            "Status": data.get("Status", "Pago"),
            "Observações": data.get("Observações", ""),
            "Mês": MONTHS_PT[now.month - 1] if "Data" not in data else "",
            "Ano": str(now.year),
            "Atualizado": now.strftime("%d/%m/%Y %H:%M"),
        }

        try:
            if "Data" in data:
                dt = datetime.strptime(data["Data"], "%d/%m/%Y")
                row["Mês"] = MONTHS_PT[dt.month - 1]
                row["Ano"] = str(dt.year)
        except (ValueError, IndexError):
            pass

        new_row_df = pd.DataFrame([row])
        self._df = pd.concat([self.dataframe, new_row_df], ignore_index=True)

        self._push_row_async(row)

        return tx_id

    def update_transaction(self, tx_id: str, data: dict):
        if self._df is None or self._df.empty:
            return

        mask = self._df["ID"] == tx_id
        if not mask.any():
            return

        now = datetime.now()
        data["Atualizado"] = now.strftime("%d/%m/%Y %H:%M")

        if "Data" in data:
            try:
                dt = datetime.strptime(data["Data"], "%d/%m/%Y")
                data["Mês"] = MONTHS_PT[dt.month - 1]
                data["Ano"] = str(dt.year)
            except (ValueError, IndexError):
                pass

        for key, value in data.items():
            if key in self._df.columns:
                self._df.loc[mask, key] = value

        self._sync_full_async()

    def delete_transaction(self, tx_id: str):
        if self._df is None:
            return
        self._df = self._df[self._df["ID"] != tx_id].reset_index(drop=True)
        self._sync_full_async()

    def bulk_add(self, rows: list[dict]):
        if not rows:
            return
        new_df = pd.DataFrame(rows)
        with self._lock:
            self._df = pd.concat([self.dataframe, new_df], ignore_index=True)
            self._sync_full_locked()

    def _as_get_records(self) -> list[dict]:
        resp = requests.get(
            self._as_url, params={"token": self._as_token}, timeout=HTTP_TIMEOUT
        )
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Apps Script: {data.get('error')}")

        headers = data.get("headers") or TRANSACTION_HEADERS
        return [dict(zip(headers, row)) for row in data.get("rows", [])]

    def _as_post(self, payload: dict):
        payload["token"] = self._as_token
        resp = requests.post(self._as_url, json=payload, timeout=HTTP_TIMEOUT)
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Apps Script: {data.get('error')}")

    def _push_row_async(self, row: dict):
        def _worker():
            with self._lock:
                if not self._connected:
                    return
                try:
                    values = _sanitize_row([row.get(h, "") for h in TRANSACTION_HEADERS])
                    if self._backend == "apps_script":
                        self._as_post({"action": "append", "row": values})
                    elif self._worksheet is not None:
                        self._worksheet.append_row(values)
                except Exception as e:
                    print(f"[SheetsSync] Erro ao enviar linha: {redact(e)}")
        threading.Thread(target=_worker, daemon=True).start()

    def _sync_full_locked(self):
        if not self._connected:
            return
        try:
            rows = []
            if self._df is not None and not self._df.empty:
                df_copy = self._df.copy()

                if "Data" in df_copy.columns:
                    df_copy["Data"] = df_copy["Data"].apply(
                        lambda x: x.strftime("%d/%m/%Y")
                        if isinstance(x, datetime) else str(x)
                    )
                rows = [
                    _sanitize_row(r)
                    for r in df_copy[TRANSACTION_HEADERS].fillna("").astype(str).values.tolist()
                ]

            if self._backend == "apps_script":
                self._as_post({"action": "replace", "rows": rows})
            elif self._worksheet is not None:

                self._worksheet.clear()
                self._worksheet.update("A1", [TRANSACTION_HEADERS])
                if rows:
                    self._worksheet.update(
                        f"A2:M{len(rows) + 1}", rows
                    )
        except Exception as e:
            print(f"[SheetsSync] Erro na sincronização completa: {redact(e)}")

    def _sync_full_async(self):
        def _worker():
            with self._lock:
                self._sync_full_locked()
        threading.Thread(target=_worker, daemon=True).start()

    def get_monthly_summary(self, year: int = None, month: int = None) -> dict:
        df = self.dataframe
        if df.empty:
            return {"receitas": 0, "despesas": 0, "saldo": 0}

        now = datetime.now()
        year = year or now.year
        month = month or now.month

        month_name = MONTHS_PT[month - 1]
        mask = (df["Mês"] == month_name) & (df["Ano"].astype(str) == str(year))
        filtered = df[mask].copy()

        if filtered.empty:
            return {"receitas": 0, "despesas": 0, "saldo": 0}

        filtered["Valor"] = pd.to_numeric(
            filtered["Valor"].astype(str).str.replace(",", ".").str.replace("R$", "").str.strip(),
            errors="coerce"
        ).fillna(0)

        receitas = filtered[filtered["Tipo"] == "Receita"]["Valor"].sum()
        despesas = filtered[filtered["Tipo"] == "Despesa"]["Valor"].sum()

        return {
            "receitas": round(receitas, 2),
            "despesas": round(despesas, 2),
            "saldo": round(receitas - despesas, 2),
        }

    def get_expenses_by_category(self, year: int = None, month: int = None) -> dict:
        df = self.dataframe
        if df.empty:
            return {}

        now = datetime.now()
        year = year or now.year
        month = month or now.month
        month_name = MONTHS_PT[month - 1]

        mask = (
            (df["Tipo"] == "Despesa")
            & (df["Mês"] == month_name)
            & (df["Ano"].astype(str) == str(year))
        )
        filtered = df[mask].copy()

        if filtered.empty:
            return {}

        filtered["Valor"] = pd.to_numeric(
            filtered["Valor"].astype(str).str.replace(",", ".").str.replace("R$", "").str.strip(),
            errors="coerce"
        ).fillna(0)

        return filtered.groupby("Categoria")["Valor"].sum().to_dict()

    def get_last_n_months_summary(self, n: int = 6) -> list[dict]:
        now = datetime.now()
        results = []
        for i in range(n - 1, -1, -1):
            month = now.month - i
            year = now.year
            while month <= 0:
                month += 12
                year -= 1
            summary = self.get_monthly_summary(year, month)
            summary["mes"] = MONTHS_PT[month - 1][:3]
            summary["mes_full"] = MONTHS_PT[month - 1]
            summary["ano"] = year
            results.append(summary)
        return results

    def get_recent_transactions(self, n: int = 10) -> list[dict]:
        df = self.dataframe
        if df.empty:
            return []

        df_sorted = df.sort_values("Data", ascending=False, na_position="last")
        return df_sorted.head(n).to_dict("records")
