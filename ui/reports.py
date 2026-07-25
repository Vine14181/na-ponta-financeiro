import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

from ui.theme import Theme
from ui.widgets import SectionHeader, EmptyState
from config import MONTHS_PT

class ReportsView(ctk.CTkFrame):

    def __init__(self, master, sync_manager, app_ref=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._sync = sync_manager
        self._app = app_ref
        self._chart_canvases = []

        self._build_ui()

    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=Theme.BORDER,
            scrollbar_button_hover_color=Theme.TEXT_MUTED,
        )
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(
            scroll, text="Relatórios",
            font=Theme.FONT_TITLE, text_color=Theme.TEXT_PRIMARY,
        ).pack(anchor="w", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_SM))

        ctk.CTkLabel(
            scroll, text="Análise detalhada das suas finanças",
            font=Theme.FONT_BODY, text_color=Theme.TEXT_SECONDARY,
        ).pack(anchor="w", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))

        SectionHeader(scroll, title="📈 Evolução Mensal").pack(
            fill="x", padx=Theme.PAD_MD, pady=Theme.PAD_SM
        )

        self._evolution_card = ctk.CTkFrame(
            scroll, fg_color=Theme.BG_SECONDARY,
            corner_radius=Theme.CARD_CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER,
        )
        self._evolution_card.pack(fill="x", padx=Theme.PAD_MD, pady=Theme.PAD_SM)

        self._evolution_container = ctk.CTkFrame(
            self._evolution_card, fg_color="transparent"
        )
        self._evolution_container.pack(fill="both", expand=True, padx=Theme.PAD_SM, pady=Theme.PAD_SM)

        SectionHeader(scroll, title="🏆 Top 5 Maiores Gastos do Mês").pack(
            fill="x", padx=Theme.PAD_MD, pady=Theme.PAD_SM
        )

        self._top5_card = ctk.CTkFrame(
            scroll, fg_color=Theme.BG_SECONDARY,
            corner_radius=Theme.CARD_CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER,
        )
        self._top5_card.pack(fill="x", padx=Theme.PAD_MD, pady=Theme.PAD_SM)

        self._top5_container = ctk.CTkFrame(
            self._top5_card, fg_color="transparent"
        )
        self._top5_container.pack(fill="both", expand=True, padx=Theme.PAD_LG, pady=Theme.PAD_MD)

        SectionHeader(scroll, title="📊 Despesas por Categoria (Barras Horizontais)").pack(
            fill="x", padx=Theme.PAD_MD, pady=Theme.PAD_SM
        )

        self._hbar_card = ctk.CTkFrame(
            scroll, fg_color=Theme.BG_SECONDARY,
            corner_radius=Theme.CARD_CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER,
        )
        self._hbar_card.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_MD))

        self._hbar_container = ctk.CTkFrame(
            self._hbar_card, fg_color="transparent"
        )
        self._hbar_container.pack(fill="both", expand=True, padx=Theme.PAD_SM, pady=Theme.PAD_SM)

        self._render_all()

    def _render_all(self):
        for canvas in self._chart_canvases:
            try:
                canvas.get_tk_widget().destroy()
            except Exception:
                pass
        self._chart_canvases.clear()

        Theme.configure_matplotlib()
        self._render_evolution_chart()
        self._render_top5()
        self._render_horizontal_bar()

    def _render_evolution_chart(self):
        for child in self._evolution_container.winfo_children():
            child.destroy()

        months_data = self._sync.get_last_n_months_summary(6)

        fig, ax = plt.subplots(figsize=(8, 3.5), dpi=100)
        fig.patch.set_facecolor(Theme.BG_SECONDARY)
        ax.set_facecolor(Theme.BG_SECONDARY)

        if months_data and any(m["receitas"] > 0 or m["despesas"] > 0 for m in months_data):
            labels = [m["mes"] for m in months_data]
            receitas = [m["receitas"] for m in months_data]
            despesas = [m["despesas"] for m in months_data]
            saldos = [m["saldo"] for m in months_data]

            x = range(len(labels))

            ax.fill_between(x, saldos, alpha=0.15, color=Theme.ACCENT)
            ax.plot(x, saldos, color=Theme.ACCENT, linewidth=2.5,
                    marker="o", markersize=6, label="Saldo", zorder=3)
            ax.plot(x, receitas, color=Theme.SUCCESS, linewidth=1.5,
                    linestyle="--", alpha=0.7, marker="s", markersize=4, label="Receitas")
            ax.plot(x, despesas, color=Theme.DANGER, linewidth=1.5,
                    linestyle="--", alpha=0.7, marker="^", markersize=4, label="Despesas")

            for i, s in enumerate(saldos):
                ax.annotate(
                    f"R${s:,.0f}", (i, s),
                    textcoords="offset points", xytext=(0, 12),
                    ha="center", fontsize=8, color=Theme.TEXT_PRIMARY,
                )

            ax.axhline(y=0, color=Theme.BORDER, linestyle="-", linewidth=0.5)
            ax.set_xticks(list(x))
            ax.set_xticklabels(labels)
            ax.legend(fontsize=8, loc="upper left")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.grid(axis="y", alpha=0.2)
        else:
            ax.text(0.5, 0.5, "Sem dados suficientes",
                    ha="center", va="center", color=Theme.TEXT_MUTED,
                    fontsize=14, transform=ax.transAxes)
            ax.axis("off")

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self._evolution_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._chart_canvases.append(canvas)
        plt.close(fig)

    def _render_top5(self):
        for child in self._top5_container.winfo_children():
            child.destroy()

        df = self._sync.dataframe
        if df.empty:
            EmptyState(
                self._top5_container, icon="📭",
                title="Sem dados para exibir"
            ).pack(fill="both", expand=True, pady=Theme.PAD_LG)
            return

        now = datetime.now()
        month_name = MONTHS_PT[now.month - 1]

        mask = (
            (df["Tipo"] == "Despesa")
            & (df["Mês"] == month_name)
            & (df["Ano"].astype(str) == str(now.year))
        )
        expenses = df[mask].copy()

        if expenses.empty:
            EmptyState(
                self._top5_container, icon="📭",
                title="Sem despesas neste mês"
            ).pack(fill="both", expand=True, pady=Theme.PAD_LG)
            return

        expenses["Valor_Num"] = expenses["Valor"].apply(
            lambda v: float(str(v).replace(",", ".").replace("R$", "").strip())
            if v else 0
        )
        top5 = expenses.nlargest(5, "Valor_Num")

        for i, (_, row) in enumerate(top5.iterrows()):
            item = ctk.CTkFrame(self._top5_container, fg_color="transparent", height=40)
            item.pack(fill="x", pady=2)
            item.pack_propagate(False)

            medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i]
            ctk.CTkLabel(
                item, text=medal, font=(Theme.FONT_FAMILY, 16), width=30,
            ).pack(side="left")

            info_frame = ctk.CTkFrame(item, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, padx=Theme.PAD_SM)

            ctk.CTkLabel(
                info_frame, text=str(row.get("Descrição", "")),
                font=Theme.FONT_BODY, text_color=Theme.TEXT_PRIMARY, anchor="w",
            ).pack(anchor="w")
            ctk.CTkLabel(
                info_frame, text=str(row.get("Categoria", "")),
                font=Theme.FONT_TINY, text_color=Theme.TEXT_MUTED, anchor="w",
            ).pack(anchor="w")

            ctk.CTkLabel(
                item, text=f"R$ {row['Valor_Num']:,.2f}",
                font=Theme.FONT_BODY_BOLD, text_color=Theme.DANGER,
            ).pack(side="right")

    def _render_horizontal_bar(self):
        for child in self._hbar_container.winfo_children():
            child.destroy()

        expenses = self._sync.get_expenses_by_category()

        fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
        fig.patch.set_facecolor(Theme.BG_SECONDARY)
        ax.set_facecolor(Theme.BG_SECONDARY)

        if expenses:

            sorted_exp = dict(sorted(expenses.items(), key=lambda x: x[1], reverse=False))

            categories = ["".join(c for c in k if ord(c) < 0x2600).strip() for k in sorted_exp.keys()]
            values = list(sorted_exp.values())
            colors = Theme.CHART_COLORS[:len(categories)]
            colors.reverse()

            bars = ax.barh(categories, values, color=colors, height=0.6,
                          edgecolor=Theme.BG_SECONDARY, linewidth=0.5)

            for bar, val in zip(bars, values):
                ax.text(
                    bar.get_width() + max(values) * 0.02,
                    bar.get_y() + bar.get_height() / 2,
                    f"R$ {val:,.0f}",
                    va="center", fontsize=9, color=Theme.TEXT_PRIMARY,
                )

            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["bottom"].set_visible(False)
            ax.xaxis.set_visible(False)
            ax.tick_params(axis="y", labelsize=9)
        else:
            ax.text(0.5, 0.5, "Sem dados", ha="center", va="center",
                    color=Theme.TEXT_MUTED, fontsize=14, transform=ax.transAxes)
            ax.axis("off")

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self._hbar_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._chart_canvases.append(canvas)
        plt.close(fig)

    def refresh(self):
        self._render_all()
