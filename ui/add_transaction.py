import customtkinter as ctk
from datetime import datetime

from ui.theme import Theme
from ui.widgets import Toast
from config import (
    EXPENSE_CATEGORIES, INCOME_CATEGORIES,
    PAYMENT_METHODS, TRANSACTION_STATUS,
)

class AddTransactionView(ctk.CTkFrame):

    def __init__(self, master, sync_manager, app_ref=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._sync = sync_manager
        self._app = app_ref

        self._build_ui()

    def _build_ui(self):

        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=Theme.BORDER,
            scrollbar_button_hover_color=Theme.TEXT_MUTED,
        )
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(
            scroll, text="Nova Transação",
            font=Theme.FONT_TITLE, text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_SM))

        ctk.CTkLabel(
            scroll, text="Preencha os dados da transação abaixo",
            font=Theme.FONT_BODY, text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))

        form_card = ctk.CTkFrame(
            scroll, fg_color=Theme.BG_SECONDARY,
            corner_radius=Theme.CARD_CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER,
        )
        form_card.pack(fill="x", padx=Theme.PAD_MD, pady=Theme.PAD_SM)

        inner = ctk.CTkFrame(form_card, fg_color="transparent")
        inner.pack(fill="x", padx=Theme.PAD_LG, pady=Theme.PAD_LG)

        row1 = ctk.CTkFrame(inner, fg_color="transparent")
        row1.pack(fill="x", pady=Theme.PAD_SM)
        row1.columnconfigure((0, 1), weight=1, uniform="field")

        self._tipo_var = ctk.StringVar(value="Despesa")

        tipo_frame = ctk.CTkFrame(row1, fg_color="transparent")
        tipo_frame.grid(row=0, column=0, padx=(0, Theme.PAD_SM), sticky="nsew")

        ctk.CTkLabel(
            tipo_frame, text="Tipo *", font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w")

        tipo_seg = ctk.CTkSegmentedButton(
            tipo_frame, values=["Despesa", "Receita"],
            variable=self._tipo_var,
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_TERTIARY,
            selected_color=Theme.ACCENT,
            selected_hover_color=Theme.ACCENT_HOVER,
            unselected_color=Theme.BG_TERTIARY,
            unselected_hover_color=Theme.BG_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            command=self._on_tipo_change,
        )
        tipo_seg.pack(fill="x", pady=(4, 0))

        data_frame = ctk.CTkFrame(row1, fg_color="transparent")
        data_frame.grid(row=0, column=1, padx=(Theme.PAD_SM, 0), sticky="nsew")

        ctk.CTkLabel(
            data_frame, text="Data *", font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w")

        self._data_entry = ctk.CTkEntry(
            data_frame,
            placeholder_text="DD/MM/AAAA",
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_TERTIARY,
            border_color=Theme.BORDER,
            text_color=Theme.TEXT_PRIMARY,
            height=Theme.INPUT_HEIGHT,
        )
        self._data_entry.pack(fill="x", pady=(4, 0))
        self._data_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))

        row2 = ctk.CTkFrame(inner, fg_color="transparent")
        row2.pack(fill="x", pady=Theme.PAD_SM)
        row2.columnconfigure((0, 1), weight=1, uniform="field")

        cat_frame = ctk.CTkFrame(row2, fg_color="transparent")
        cat_frame.grid(row=0, column=0, padx=(0, Theme.PAD_SM), sticky="nsew")

        ctk.CTkLabel(
            cat_frame, text="Categoria *", font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w")

        self._cat_var = ctk.StringVar(value="")
        self._cat_dropdown = ctk.CTkComboBox(
            cat_frame,
            values=list(EXPENSE_CATEGORIES.keys()),
            variable=self._cat_var,
            font=Theme.FONT_BODY,
            dropdown_font=Theme.FONT_BODY,
            fg_color=Theme.BG_TERTIARY,
            border_color=Theme.BORDER,
            button_color=Theme.ACCENT,
            button_hover_color=Theme.ACCENT_HOVER,
            dropdown_fg_color=Theme.BG_SECONDARY,
            dropdown_hover_color=Theme.BG_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            dropdown_text_color=Theme.TEXT_PRIMARY,
            height=Theme.INPUT_HEIGHT,
            state="readonly",
            command=self._on_category_change,
        )
        self._cat_dropdown.pack(fill="x", pady=(4, 0))
        self._cat_dropdown.set("")

        subcat_frame = ctk.CTkFrame(row2, fg_color="transparent")
        subcat_frame.grid(row=0, column=1, padx=(Theme.PAD_SM, 0), sticky="nsew")

        ctk.CTkLabel(
            subcat_frame, text="Subcategoria", font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w")

        self._subcat_var = ctk.StringVar(value="")
        self._subcat_dropdown = ctk.CTkComboBox(
            subcat_frame,
            values=[""],
            variable=self._subcat_var,
            font=Theme.FONT_BODY,
            dropdown_font=Theme.FONT_BODY,
            fg_color=Theme.BG_TERTIARY,
            border_color=Theme.BORDER,
            button_color=Theme.ACCENT,
            button_hover_color=Theme.ACCENT_HOVER,
            dropdown_fg_color=Theme.BG_SECONDARY,
            dropdown_hover_color=Theme.BG_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            dropdown_text_color=Theme.TEXT_PRIMARY,
            height=Theme.INPUT_HEIGHT,
            state="readonly",
        )
        self._subcat_dropdown.pack(fill="x", pady=(4, 0))

        row3 = ctk.CTkFrame(inner, fg_color="transparent")
        row3.pack(fill="x", pady=Theme.PAD_SM)
        row3.columnconfigure(0, weight=2)
        row3.columnconfigure(1, weight=1)

        desc_frame = ctk.CTkFrame(row3, fg_color="transparent")
        desc_frame.grid(row=0, column=0, padx=(0, Theme.PAD_SM), sticky="nsew")

        ctk.CTkLabel(
            desc_frame, text="Descrição *", font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w")

        self._desc_entry = ctk.CTkEntry(
            desc_frame,
            placeholder_text="Ex: Almoço no restaurante",
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_TERTIARY,
            border_color=Theme.BORDER,
            text_color=Theme.TEXT_PRIMARY,
            height=Theme.INPUT_HEIGHT,
        )
        self._desc_entry.pack(fill="x", pady=(4, 0))

        val_frame = ctk.CTkFrame(row3, fg_color="transparent")
        val_frame.grid(row=0, column=1, padx=(Theme.PAD_SM, 0), sticky="nsew")

        ctk.CTkLabel(
            val_frame, text="Valor (R$) *", font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w")

        self._valor_entry = ctk.CTkEntry(
            val_frame,
            placeholder_text="0,00",
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_TERTIARY,
            border_color=Theme.BORDER,
            text_color=Theme.TEXT_PRIMARY,
            height=Theme.INPUT_HEIGHT,
        )
        self._valor_entry.pack(fill="x", pady=(4, 0))

        row4 = ctk.CTkFrame(inner, fg_color="transparent")
        row4.pack(fill="x", pady=Theme.PAD_SM)
        row4.columnconfigure((0, 1), weight=1, uniform="field")

        pay_frame = ctk.CTkFrame(row4, fg_color="transparent")
        pay_frame.grid(row=0, column=0, padx=(0, Theme.PAD_SM), sticky="nsew")

        ctk.CTkLabel(
            pay_frame, text="Método de Pagamento", font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w")

        self._pay_var = ctk.StringVar(value="Pix")
        ctk.CTkComboBox(
            pay_frame,
            values=PAYMENT_METHODS,
            variable=self._pay_var,
            font=Theme.FONT_BODY,
            dropdown_font=Theme.FONT_BODY,
            fg_color=Theme.BG_TERTIARY,
            border_color=Theme.BORDER,
            button_color=Theme.ACCENT,
            button_hover_color=Theme.ACCENT_HOVER,
            dropdown_fg_color=Theme.BG_SECONDARY,
            dropdown_hover_color=Theme.BG_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            dropdown_text_color=Theme.TEXT_PRIMARY,
            height=Theme.INPUT_HEIGHT,
            state="readonly",
        ).pack(fill="x", pady=(4, 0))

        status_frame = ctk.CTkFrame(row4, fg_color="transparent")
        status_frame.grid(row=0, column=1, padx=(Theme.PAD_SM, 0), sticky="nsew")

        ctk.CTkLabel(
            status_frame, text="Status", font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w")

        self._status_var = ctk.StringVar(value="Pago")
        ctk.CTkComboBox(
            status_frame,
            values=TRANSACTION_STATUS,
            variable=self._status_var,
            font=Theme.FONT_BODY,
            dropdown_font=Theme.FONT_BODY,
            fg_color=Theme.BG_TERTIARY,
            border_color=Theme.BORDER,
            button_color=Theme.ACCENT,
            button_hover_color=Theme.ACCENT_HOVER,
            dropdown_fg_color=Theme.BG_SECONDARY,
            dropdown_hover_color=Theme.BG_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            dropdown_text_color=Theme.TEXT_PRIMARY,
            height=Theme.INPUT_HEIGHT,
            state="readonly",
        ).pack(fill="x", pady=(4, 0))

        obs_frame = ctk.CTkFrame(inner, fg_color="transparent")
        obs_frame.pack(fill="x", pady=Theme.PAD_SM)

        ctk.CTkLabel(
            obs_frame, text="Observações", font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w")

        self._obs_entry = ctk.CTkTextbox(
            obs_frame,
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_TERTIARY,
            border_color=Theme.BORDER,
            text_color=Theme.TEXT_PRIMARY,
            height=80,
            corner_radius=Theme.BUTTON_CORNER_RADIUS,
            border_width=1,
        )
        self._obs_entry.pack(fill="x", pady=(4, 0))

        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(Theme.PAD_LG, Theme.PAD_SM))

        ctk.CTkButton(
            btn_frame,
            text="💾  Salvar Transação",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.ACCENT,
            hover_color=Theme.ACCENT_HOVER,
            text_color="#FFFFFF",
            height=44,
            corner_radius=Theme.BUTTON_CORNER_RADIUS,
            command=self._save_transaction,
        ).pack(side="left", padx=(0, Theme.PAD_SM))

        ctk.CTkButton(
            btn_frame,
            text="🗑️  Limpar",
            font=Theme.FONT_BODY,
            fg_color="transparent",
            hover_color=Theme.BG_HOVER,
            text_color=Theme.TEXT_SECONDARY,
            border_width=1,
            border_color=Theme.BORDER,
            height=44,
            corner_radius=Theme.BUTTON_CORNER_RADIUS,
            command=self._clear_form,
        ).pack(side="left")

    def _on_tipo_change(self, value):
        if value == "Receita":
            categories = list(INCOME_CATEGORIES.keys())
        else:
            categories = list(EXPENSE_CATEGORIES.keys())

        self._cat_dropdown.configure(values=categories)
        self._cat_var.set("")
        self._subcat_dropdown.configure(values=[""])
        self._subcat_var.set("")

    def _on_category_change(self, value):
        tipo = self._tipo_var.get()
        cats = INCOME_CATEGORIES if tipo == "Receita" else EXPENSE_CATEGORIES

        subcats = cats.get(value, [])
        self._subcat_dropdown.configure(values=subcats if subcats else [""])
        if subcats:
            self._subcat_var.set(subcats[0])
        else:
            self._subcat_var.set("")

    def _save_transaction(self):

        data = self._data_entry.get().strip()
        categoria = self._cat_var.get().strip()
        descricao = self._desc_entry.get().strip()
        valor = self._valor_entry.get().strip()

        if not data:
            Toast(self.winfo_toplevel(), "Preencha a data!", "error")
            return
        if not categoria:
            Toast(self.winfo_toplevel(), "Selecione uma categoria!", "error")
            return
        if not descricao:
            Toast(self.winfo_toplevel(), "Preencha a descrição!", "error")
            return
        if not valor:
            Toast(self.winfo_toplevel(), "Preencha o valor!", "error")
            return

        try:
            datetime.strptime(data, "%d/%m/%Y")
        except ValueError:
            Toast(self.winfo_toplevel(), "Data inválida! Use DD/MM/AAAA", "error")
            return

        try:
            valor_clean = valor.replace(",", ".").replace("R$", "").strip()
            float(valor_clean)
        except ValueError:
            Toast(self.winfo_toplevel(), "Valor inválido!", "error")
            return

        tx_data = {
            "Data": data,
            "Tipo": self._tipo_var.get(),
            "Categoria": categoria,
            "Subcategoria": self._subcat_var.get(),
            "Descrição": descricao,
            "Valor": valor_clean,
            "Método Pagamento": self._pay_var.get(),
            "Status": self._status_var.get(),
            "Observações": self._obs_entry.get("1.0", "end").strip(),
        }

        tx_id = self._sync.add_transaction(tx_data)
        Toast(self.winfo_toplevel(), f"Transação {tx_id} salva com sucesso!", "success")
        self._clear_form()

        if self._app:
            self._app.refresh_dashboard()

    def _clear_form(self):
        self._tipo_var.set("Despesa")
        self._data_entry.delete(0, "end")
        self._data_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self._cat_var.set("")
        self._subcat_var.set("")
        self._desc_entry.delete(0, "end")
        self._valor_entry.delete(0, "end")
        self._pay_var.set("Pix")
        self._status_var.set("Pago")
        self._obs_entry.delete("1.0", "end")
        self._on_tipo_change("Despesa")

    def refresh(self):
        pass
