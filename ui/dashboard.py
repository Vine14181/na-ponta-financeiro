import threading

import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

from ui.theme import Theme
from ui.widgets import MetricCard, SectionHeader, EmptyState, StatusBadge, Toast
from config import MONTHS_PT
from pierre_client import PierreClient, import_from_pierre

class DashboardView(ctk.CTkFrame):

    def __init__(self, master, sync_manager, app_ref=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._sync = sync_manager
        self._app = app_ref
        self._chart_canvases = []

        self._build_ui()

    def _build_ui(self):

        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=Theme.BORDER,
            scrollbar_button_hover_color=Theme.TEXT_MUTED,
        )
        self._scroll.pack(fill="both", expand=True)

        header = ctk.CTkFrame(self._scroll, fg_color="transparent")
        header.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_SM))

        now = datetime.now()
        month_name = MONTHS_PT[now.month - 1]

        ctk.CTkLabel(
            header, text="Dashboard",
            font=Theme.FONT_TITLE, text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")

        ctk.CTkLabel(
            header, text=f"{month_name} {now.year}",
            font=Theme.FONT_BODY, text_color=Theme.TEXT_SECONDARY
        ).pack(side="right")

        self._import_btn = ctk.CTkButton(
            header, text="⬇️  Importar do Pierre",
            font=Theme.FONT_SMALL,
            fg_color=Theme.ACCENT,
            hover_color=Theme.ACCENT_HOVER,
            text_color="#FFFFFF",
            height=32, width=160,
            corner_radius=6,
            command=self._import_pierre,
        )
        self._import_btn.pack(side="right", padx=(0, Theme.PAD_MD))

        cards_frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        cards_frame.pack(fill="x", padx=Theme.PAD_MD, pady=Theme.PAD_SM)
        cards_frame.columnconfigure((0, 1, 2), weight=1, uniform="card")

        summary = self._sync.get_monthly_summary()

        self._card_balance = MetricCard(
            cards_frame, icon="💰", label="Saldo do Mês",
            value=self._format_currency(summary["saldo"]),
            color=Theme.SUCCESS if summary["saldo"] >= 0 else Theme.DANGER,
        )
        self._card_balance.grid(row=0, column=0, padx=(0, Theme.PAD_SM), sticky="nsew")

        self._card_income = MetricCard(
            cards_frame, icon="📈", label="Receitas",
            value=self._format_currency(summary["receitas"]),
            color=Theme.SUCCESS,
        )
        self._card_income.grid(row=0, column=1, padx=Theme.PAD_SM, sticky="nsew")

        self._card_expense = MetricCard(
            cards_frame, icon="📉", label="Despesas",
            value=self._format_currency(summary["despesas"]),
            color=Theme.DANGER,
        )
        self._card_expense.grid(row=0, column=2, padx=(Theme.PAD_SM, 0), sticky="nsew")

        self._banks_frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._banks_frame.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, 0))
        self._load_balances_async()

        charts_frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        charts_frame.pack(fill="x", padx=Theme.PAD_MD, pady=Theme.PAD_SM)
        charts_frame.columnconfigure((0, 1), weight=1, uniform="chart")

        pie_card = ctk.CTkFrame(
            charts_frame, fg_color=Theme.BG_SECONDARY,
            corner_radius=Theme.CARD_CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER
        )
        pie_card.grid(row=0, column=0, padx=(0, Theme.PAD_SM), sticky="nsew")

        ctk.CTkLabel(
            pie_card, text="  Despesas por Categoria",
            font=Theme.FONT_HEADING, text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, 0))

        self._pie_container = ctk.CTkFrame(pie_card, fg_color="transparent")
        self._pie_container.pack(fill="both", expand=True, padx=Theme.PAD_SM, pady=Theme.PAD_SM)

        bar_card = ctk.CTkFrame(
            charts_frame, fg_color=Theme.BG_SECONDARY,
            corner_radius=Theme.CARD_CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER
        )
        bar_card.grid(row=0, column=1, padx=(Theme.PAD_SM, 0), sticky="nsew")

        ctk.CTkLabel(
            bar_card, text="  Receita vs Despesa",
            font=Theme.FONT_HEADING, text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, 0))

        self._bar_container = ctk.CTkFrame(bar_card, fg_color="transparent")
        self._bar_container.pack(fill="both", expand=True, padx=Theme.PAD_SM, pady=Theme.PAD_SM)

        SectionHeader(
            self._scroll, title="Transações Recentes",
            action_text="Ver Todas →",
            action_command=lambda: self._app.navigate("transactions") if self._app else None,
        ).pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_SM))

        self._transactions_container = ctk.CTkFrame(
            self._scroll, fg_color=Theme.BG_SECONDARY,
            corner_radius=Theme.CARD_CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER,
        )
        self._transactions_container.pack(
            fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD)
        )

        self._render_charts()
        self._render_recent_transactions()

    def _render_charts(self):

        for canvas in self._chart_canvases:
            try:
                canvas.get_tk_widget().destroy()
            except Exception:
                pass
        self._chart_canvases.clear()

        Theme.configure_matplotlib()

        expenses = self._sync.get_expenses_by_category()

        fig_pie, ax_pie = plt.subplots(figsize=(4, 3), dpi=100)
        fig_pie.patch.set_facecolor(Theme.BG_SECONDARY)
        ax_pie.set_facecolor(Theme.BG_SECONDARY)

        if expenses:
            labels = [self._strip_emoji(l) for l in expenses.keys()]
            sizes = list(expenses.values())
            colors = Theme.CHART_COLORS[:len(labels)]

            wedges, texts, autotexts = ax_pie.pie(
                sizes, labels=None, autopct="%1.0f%%",
                colors=colors, startangle=90,
                textprops={"color": Theme.TEXT_PRIMARY, "fontsize": 9},
                pctdistance=0.8,
                wedgeprops={"linewidth": 1, "edgecolor": Theme.BG_SECONDARY},
            )
            for autotext in autotexts:
                autotext.set_fontsize(8)

            ax_pie.legend(
                wedges, [f"{l} (R${v:,.0f})" for l, v in zip(labels, sizes)],
                loc="center left", bbox_to_anchor=(-0.1, -0.15),
                fontsize=7, ncol=2,
                frameon=False,
                labelcolor=Theme.TEXT_SECONDARY,
            )
        else:
            ax_pie.text(
                0.5, 0.5, "Sem dados",
                ha="center", va="center",
                color=Theme.TEXT_MUTED, fontsize=14,
                transform=ax_pie.transAxes,
            )
            ax_pie.set_xlim(0, 1)
            ax_pie.set_ylim(0, 1)
            ax_pie.axis("off")

        fig_pie.tight_layout()
        canvas_pie = FigureCanvasTkAgg(fig_pie, master=self._pie_container)
        canvas_pie.draw()
        canvas_pie.get_tk_widget().pack(fill="both", expand=True)
        self._chart_canvases.append(canvas_pie)
        plt.close(fig_pie)

        months_data = self._sync.get_last_n_months_summary(6)

        fig_bar, ax_bar = plt.subplots(figsize=(4, 3), dpi=100)
        fig_bar.patch.set_facecolor(Theme.BG_SECONDARY)
        ax_bar.set_facecolor(Theme.BG_SECONDARY)

        if months_data and any(m["receitas"] > 0 or m["despesas"] > 0 for m in months_data):
            labels_bar = [m["mes"] for m in months_data]
            receitas = [m["receitas"] for m in months_data]
            despesas = [m["despesas"] for m in months_data]

            x = range(len(labels_bar))
            width = 0.35

            bars1 = ax_bar.bar(
                [i - width / 2 for i in x], receitas, width,
                label="Receitas", color=Theme.SUCCESS, alpha=0.85,
                edgecolor=Theme.BG_SECONDARY, linewidth=0.5,
            )
            bars2 = ax_bar.bar(
                [i + width / 2 for i in x], despesas, width,
                label="Despesas", color=Theme.DANGER, alpha=0.85,
                edgecolor=Theme.BG_SECONDARY, linewidth=0.5,
            )

            ax_bar.set_xticks(list(x))
            ax_bar.set_xticklabels(labels_bar, fontsize=9)
            ax_bar.legend(fontsize=8, loc="upper left")
            ax_bar.spines["top"].set_visible(False)
            ax_bar.spines["right"].set_visible(False)
            ax_bar.grid(axis="y", alpha=0.3)
        else:
            ax_bar.text(
                0.5, 0.5, "Sem dados",
                ha="center", va="center",
                color=Theme.TEXT_MUTED, fontsize=14,
                transform=ax_bar.transAxes,
            )
            ax_bar.axis("off")

        fig_bar.tight_layout()
        canvas_bar = FigureCanvasTkAgg(fig_bar, master=self._bar_container)
        canvas_bar.draw()
        canvas_bar.get_tk_widget().pack(fill="both", expand=True)
        self._chart_canvases.append(canvas_bar)
        plt.close(fig_bar)

    def _render_recent_transactions(self):

        for child in self._transactions_container.winfo_children():
            child.destroy()

        transactions = self._sync.get_recent_transactions(8)

        if not transactions:
            EmptyState(
                self._transactions_container,
                icon="📭", title="Nenhuma transação ainda",
                subtitle="Adicione sua primeira transação!"
            ).pack(fill="both", expand=True, pady=Theme.PAD_XL)
            return

        header = ctk.CTkFrame(self._transactions_container, fg_color=Theme.BG_TERTIARY, height=36)
        header.pack(fill="x", padx=1, pady=(1, 0))
        header.pack_propagate(False)

        cols = [("Data", 0.12), ("Tipo", 0.08), ("Categoria", 0.2),
                ("Descrição", 0.28), ("Valor", 0.14), ("Status", 0.1)]

        for col_name, weight in cols:
            ctk.CTkLabel(
                header, text=col_name, font=Theme.FONT_SMALL,
                text_color=Theme.TEXT_MUTED, anchor="w"
            ).pack(side="left", padx=Theme.PAD_SM, expand=True, fill="x")

        for i, tx in enumerate(transactions):
            row_bg = "transparent" if i % 2 == 0 else Theme.BG_TERTIARY
            row = ctk.CTkFrame(self._transactions_container, fg_color=row_bg, height=40)
            row.pack(fill="x", padx=1)
            row.pack_propagate(False)

            date_str = ""
            if isinstance(tx.get("Data"), datetime):
                date_str = tx["Data"].strftime("%d/%m/%Y")
            elif tx.get("Data"):
                date_str = str(tx["Data"])[:10]

            ctk.CTkLabel(
                row, text=date_str, font=Theme.FONT_SMALL,
                text_color=Theme.TEXT_SECONDARY, anchor="w"
            ).pack(side="left", padx=Theme.PAD_SM, expand=True, fill="x")

            tipo = str(tx.get("Tipo", ""))
            tipo_color = Theme.SUCCESS if tipo == "Receita" else Theme.DANGER
            ctk.CTkLabel(
                row, text=tipo, font=Theme.FONT_SMALL,
                text_color=tipo_color, anchor="w"
            ).pack(side="left", padx=Theme.PAD_SM, expand=True, fill="x")

            ctk.CTkLabel(
                row, text=str(tx.get("Categoria", "")), font=Theme.FONT_SMALL,
                text_color=Theme.TEXT_PRIMARY, anchor="w"
            ).pack(side="left", padx=Theme.PAD_SM, expand=True, fill="x")

            ctk.CTkLabel(
                row, text=str(tx.get("Descrição", "")), font=Theme.FONT_SMALL,
                text_color=Theme.TEXT_SECONDARY, anchor="w"
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
                font=Theme.FONT_SMALL, text_color=valor_color, anchor="w"
            ).pack(side="left", padx=Theme.PAD_SM, expand=True, fill="x")

            status = str(tx.get("Status", "Pago"))
            StatusBadge(row, status).pack(side="left", padx=Theme.PAD_SM)

    def _import_pierre(self):
        client = PierreClient()
        if not client.is_configured:
            Toast(
                self.winfo_toplevel(),
                "Configure a chave do Pierre em Configurações → Cofre de API Keys",
                "warning"
            )
            return

        self._import_btn.configure(state="disabled", text="⏳  Importando...")
        Toast(self.winfo_toplevel(), "Buscando transações dos seus bancos...", "info", duration=2500)

        def _worker():
            try:
                stats = import_from_pierre(self._sync, days=30)
            except Exception as e:
                self.after(0, lambda e=e: self._on_import_done(erro=str(e)))
                return
            self.after(0, lambda: self._on_import_done(stats=stats))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_import_done(self, stats: dict = None, erro: str = None):
        try:
            self._import_btn.configure(state="normal", text="⬇️  Importar do Pierre")
        except Exception:
            return

        if erro:
            Toast(self.winfo_toplevel(), f"Erro na importação: {erro}", "error")
            return

        partes = [f"✅ {stats['importadas']} transações importadas"]
        if stats["duplicadas"]:
            partes.append(f"{stats['duplicadas']} já existiam")
        if stats["ignoradas"]:
            partes.append(f"{stats['ignoradas']} transferências internas ignoradas")
        Toast(self.winfo_toplevel(), " • ".join(partes), "success")

        self.refresh()

    def _load_balances_async(self):
        def _worker():
            try:
                client = PierreClient()
                if not client.is_configured:
                    return
                data = client.get_balance()
            except Exception as e:
                print(f"[Dashboard] Erro ao buscar saldos do Pierre: {e}")
                return
            try:
                self.after(0, lambda: self._render_balances(data))
            except RuntimeError:
                pass
        threading.Thread(target=_worker, daemon=True).start()

    def _render_balances(self, data: dict):
        try:
            for child in self._banks_frame.winfo_children():
                child.destroy()
        except Exception:
            return

        accounts = data.get("accounts") or []
        if not accounts:
            return

        cols = len(accounts) + 1
        self._banks_frame.columnconfigure(tuple(range(cols)), weight=1, uniform="bank")

        total = float(data.get("total_balance") or 0)
        card_total = MetricCard(
            self._banks_frame, icon="🏦", label="Saldo Total (bancos)",
            value=self._format_currency(total),
            color=Theme.SUCCESS if total >= 0 else Theme.DANGER,
        )
        card_total.grid(row=0, column=0, padx=(0, Theme.PAD_SM), sticky="nsew")

        for i, acc in enumerate(accounts):
            saldo = float(acc.get("balance") or 0)
            nome = str(acc.get("name") or "Conta")[:22]
            card = MetricCard(
                self._banks_frame, icon="💳", label=nome,
                value=self._format_currency(saldo),
                color=Theme.SUCCESS if saldo >= 0 else Theme.DANGER,
            )
            padx = (Theme.PAD_SM, 0) if i == len(accounts) - 1 else Theme.PAD_SM
            card.grid(row=0, column=i + 1, padx=padx, sticky="nsew")

    def refresh(self):
        summary = self._sync.get_monthly_summary()

        saldo_color = Theme.SUCCESS if summary["saldo"] >= 0 else Theme.DANGER
        self._card_balance.update_value(
            self._format_currency(summary["saldo"]), saldo_color
        )
        self._card_income.update_value(self._format_currency(summary["receitas"]))
        self._card_expense.update_value(self._format_currency(summary["despesas"]))

        self._render_charts()
        self._render_recent_transactions()
        self._load_balances_async()

    @staticmethod
    def _strip_emoji(text: str) -> str:
        return "".join(c for c in str(text) if ord(c) < 0x2600).strip()

    @staticmethod
    def _format_currency(value: float) -> str:
        if value < 0:
            return f"- R$ {abs(value):,.2f}"
        return f"R$ {value:,.2f}"
