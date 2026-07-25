import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox

from ui.theme import Theme
from ui.widgets import SearchBar, FilterDropdown, EmptyState, StatusBadge, Toast
from config import (
    EXPENSE_CATEGORIES, INCOME_CATEGORIES,
    MONTHS_PT, TRANSACTION_STATUS,
)

class TransactionsView(ctk.CTkFrame):

    def __init__(self, master, sync_manager, app_ref=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._sync = sync_manager
        self._app = app_ref
        self._filtered_data = []

        self._build_ui()

    def _build_ui(self):

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_SM))

        ctk.CTkLabel(
            header, text="Transações",
            font=Theme.FONT_TITLE, text_color=Theme.TEXT_PRIMARY,
        ).pack(side="left")

        self._count_label = ctk.CTkLabel(
            header, text="0 transações", font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY,
        )
        self._count_label.pack(side="right")

        self._search = SearchBar(
            self, placeholder="Buscar por descrição, categoria...",
            on_search=self._apply_filters,
        )
        self._search.pack(fill="x", padx=Theme.PAD_MD, pady=Theme.PAD_SM)

        filters_frame = ctk.CTkFrame(self, fg_color="transparent")
        filters_frame.pack(fill="x", padx=Theme.PAD_MD, pady=Theme.PAD_SM)

        all_categories = list(EXPENSE_CATEGORIES.keys()) + list(INCOME_CATEGORIES.keys())

        self._filter_tipo = FilterDropdown(
            filters_frame, "Tipo", ["Receita", "Despesa"],
            on_change=lambda _: self._apply_filters(),
        )
        self._filter_tipo.pack(side="left", padx=(0, Theme.PAD_SM), fill="x", expand=True)

        self._filter_cat = FilterDropdown(
            filters_frame, "Categoria", all_categories,
            on_change=lambda _: self._apply_filters(),
        )
        self._filter_cat.pack(side="left", padx=Theme.PAD_SM, fill="x", expand=True)

        self._filter_mes = FilterDropdown(
            filters_frame, "Mês", MONTHS_PT,
            on_change=lambda _: self._apply_filters(),
        )
        self._filter_mes.pack(side="left", padx=Theme.PAD_SM, fill="x", expand=True)

        self._filter_status = FilterDropdown(
            filters_frame, "Status", TRANSACTION_STATUS,
            on_change=lambda _: self._apply_filters(),
        )
        self._filter_status.pack(side="left", padx=(Theme.PAD_SM, 0), fill="x", expand=True)

        ctk.CTkButton(
            filters_frame, text="✕", width=32, height=32,
            font=Theme.FONT_BODY,
            fg_color="transparent",
            hover_color=Theme.BG_HOVER,
            text_color=Theme.TEXT_MUTED,
            corner_radius=6,
            command=self._clear_filters,
        ).pack(side="left", padx=(Theme.PAD_SM, 0), pady=(16, 0))

        table_card = ctk.CTkFrame(
            self, fg_color=Theme.BG_SECONDARY,
            corner_radius=Theme.CARD_CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER,
        )
        table_card.pack(fill="both", expand=True, padx=Theme.PAD_MD, pady=Theme.PAD_SM)

        self._table_header = ctk.CTkFrame(table_card, fg_color=Theme.BG_TERTIARY, height=36)
        self._table_header.pack(fill="x", padx=1, pady=(1, 0))
        self._table_header.pack_propagate(False)

        cols = ["Data", "Tipo", "Categoria", "Descrição", "Valor", "Pagamento", "Status", "Ações"]
        for col in cols:
            ctk.CTkLabel(
                self._table_header, text=col, font=Theme.FONT_SMALL,
                text_color=Theme.TEXT_MUTED, anchor="w",
            ).pack(side="left", padx=Theme.PAD_SM, expand=True, fill="x")

        self._table_body = ctk.CTkScrollableFrame(
            table_card, fg_color="transparent",
            scrollbar_button_color=Theme.BORDER,
            scrollbar_button_hover_color=Theme.TEXT_MUTED,
        )
        self._table_body.pack(fill="both", expand=True, padx=1, pady=(0, 1))

        self._apply_filters()

    def _apply_filters(self, search_text: str = None):
        df = self._sync.dataframe
        if df.empty:
            self._filtered_data = []
            self._render_table()
            return

        filtered = df.copy()

        if search_text is None:
            search_text = self._search.get()
        if search_text:
            search_lower = search_text.lower()
            mask = (
                filtered["Descrição"].astype(str).str.lower().str.contains(search_lower, na=False)
                | filtered["Categoria"].astype(str).str.lower().str.contains(search_lower, na=False)
                | filtered["Observações"].astype(str).str.lower().str.contains(search_lower, na=False)
            )
            filtered = filtered[mask]

        tipo = self._filter_tipo.get()
        if tipo != "Todos":
            filtered = filtered[filtered["Tipo"] == tipo]

        cat = self._filter_cat.get()
        if cat != "Todos":
            filtered = filtered[filtered["Categoria"] == cat]

        mes = self._filter_mes.get()
        if mes != "Todos":
            filtered = filtered[filtered["Mês"] == mes]

        status = self._filter_status.get()
        if status != "Todos":
            filtered = filtered[filtered["Status"] == status]

        filtered = filtered.sort_values("Data", ascending=False, na_position="last")

        self._filtered_data = filtered.to_dict("records")
        self._render_table()

    def _render_table(self):

        for child in self._table_body.winfo_children():
            child.destroy()

        self._count_label.configure(text=f"{len(self._filtered_data)} transações")

        if not self._filtered_data:
            EmptyState(
                self._table_body,
                icon="🔍", title="Nenhuma transação encontrada",
                subtitle="Tente ajustar os filtros"
            ).pack(fill="both", expand=True, pady=Theme.PAD_XL)
            return

        for i, tx in enumerate(self._filtered_data):
            row_bg = "transparent" if i % 2 == 0 else Theme.BG_TERTIARY
            row = ctk.CTkFrame(self._table_body, fg_color=row_bg, height=40)
            row.pack(fill="x")
            row.pack_propagate(False)

            date_str = ""
            if isinstance(tx.get("Data"), datetime):
                date_str = tx["Data"].strftime("%d/%m/%Y")
            elif tx.get("Data"):
                date_str = str(tx["Data"])[:10]

            ctk.CTkLabel(
                row, text=date_str, font=Theme.FONT_SMALL,
                text_color=Theme.TEXT_SECONDARY, anchor="w",
            ).pack(side="left", padx=Theme.PAD_SM, expand=True, fill="x")

            tipo = str(tx.get("Tipo", ""))
            tipo_color = Theme.SUCCESS if tipo == "Receita" else Theme.DANGER
            ctk.CTkLabel(
                row, text=tipo, font=Theme.FONT_SMALL,
                text_color=tipo_color, anchor="w",
            ).pack(side="left", padx=Theme.PAD_SM, expand=True, fill="x")

            ctk.CTkLabel(
                row, text=str(tx.get("Categoria", "")), font=Theme.FONT_SMALL,
                text_color=Theme.TEXT_PRIMARY, anchor="w",
            ).pack(side="left", padx=Theme.PAD_SM, expand=True, fill="x")

            ctk.CTkLabel(
                row, text=str(tx.get("Descrição", "")), font=Theme.FONT_SMALL,
                text_color=Theme.TEXT_SECONDARY, anchor="w",
            ).pack(side="left", padx=Theme.PAD_SM, expand=True, fill="x")

            valor = tx.get("Valor", 0)
            try:
                valor_num = float(str(valor).replace(",", ".").replace("R$", "").strip())
            except (ValueError, TypeError):
                valor_num = 0
            valor_color = Theme.SUCCESS if tipo == "Receita" else Theme.DANGER
            prefix = "+" if tipo == "Receita" else "-"
            ctk.CTkLabel(
                row, text=f"{prefix} R$ {abs(valor_num):,.2f}",
                font=Theme.FONT_SMALL, text_color=valor_color, anchor="w",
            ).pack(side="left", padx=Theme.PAD_SM, expand=True, fill="x")

            ctk.CTkLabel(
                row, text=str(tx.get("Método Pagamento", "")),
                font=Theme.FONT_SMALL, text_color=Theme.TEXT_SECONDARY, anchor="w",
            ).pack(side="left", padx=Theme.PAD_SM, expand=True, fill="x")

            status = str(tx.get("Status", "Pago"))
            StatusBadge(row, status).pack(side="left", padx=Theme.PAD_SM)

            tx_id = str(tx.get("ID", ""))
            actions_frame = ctk.CTkFrame(row, fg_color="transparent")
            actions_frame.pack(side="left", padx=Theme.PAD_SM)

            ctk.CTkButton(
                actions_frame, text="🗑️", width=28, height=28,
                font=(Theme.FONT_FAMILY, 12),
                fg_color="transparent",
                hover_color=Theme.DANGER_DIM,
                text_color=Theme.DANGER,
                corner_radius=4,
                command=lambda tid=tx_id: self._delete_transaction(tid),
            ).pack(side="left")

    def _delete_transaction(self, tx_id: str):
        if messagebox.askyesno("Confirmar Exclusão",
                               f"Deseja excluir a transação {tx_id}?"):
            self._sync.delete_transaction(tx_id)
            Toast(self.winfo_toplevel(), f"Transação {tx_id} excluída!", "success")
            self._apply_filters()
            if self._app:
                self._app.refresh_dashboard()

    def _clear_filters(self):
        self._search.clear()
        self._filter_tipo.reset()
        self._filter_cat.reset()
        self._filter_mes.reset()
        self._filter_status.reset()
        self._apply_filters()

    def refresh(self):
        self._apply_filters()
