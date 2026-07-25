import customtkinter as ctk

from ui.theme import Theme
from ui.widgets import NavButton, Toast
from ui.dashboard import DashboardView
from ui.add_transaction import AddTransactionView
from ui.transactions import TransactionsView
from ui.reports import ReportsView
from ui.advisor import AdvisorView
from ui.technician import TechnicianView
from ui.pierre_chat import PierreChatView
from ui.settings import SettingsView
from sheets_sync import SheetsSync

class NaPontaApp(ctk.CTk):

    def __init__(self, sync: SheetsSync):
        super().__init__()

        self._sync = sync
        self._current_view = None
        self._nav_buttons: dict[str, NavButton] = {}
        self._views: dict[str, ctk.CTkFrame] = {}

        self.title("Na Ponta — Controle Financeiro")
        self.geometry("1280x780")
        self.minsize(1000, 600)
        self._set_window_icon()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=Theme.BG_PRIMARY)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content_area()

        self.navigate("dashboard")

        if self._sync.is_connected:
            self._sync.pull_async(callback=lambda _: self.after(0, self._on_data_loaded))

    def _set_window_icon(self):
        import os
        from config import APP_DIR, DATA_DIR
        candidatos = [
            os.path.join(DATA_DIR, "na_ponta.ico"),
            os.path.join(APP_DIR, "na_ponta.ico"),
        ]
        ico = next((c for c in candidatos if os.path.exists(c)), None)
        if not ico:
            return
        try:
            self.iconbitmap(ico)
        except Exception:
            pass

        self.after(300, lambda: self._reapply_icon(ico))

    def _reapply_icon(self, ico):
        try:
            self.iconbitmap(ico)
        except Exception:
            pass

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(
            self, fg_color=Theme.BG_SECONDARY,
            width=Theme.SIDEBAR_WIDTH,
            corner_radius=0,
            border_width=0,
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_LG, Theme.PAD_SM))

        ctk.CTkLabel(
            logo_frame, text="💰",
            font=(Theme.FONT_FAMILY, 32),
        ).pack(side="left")

        name_frame = ctk.CTkFrame(logo_frame, fg_color="transparent")
        name_frame.pack(side="left", padx=(Theme.PAD_SM, 0))

        ctk.CTkLabel(
            name_frame, text="Na Ponta",
            font=(Theme.FONT_FAMILY, 20, "bold"),
            text_color=Theme.TEXT_PRIMARY,
        ).pack(anchor="w")

        ctk.CTkLabel(
            name_frame, text="Controle Financeiro",
            font=Theme.FONT_TINY,
            text_color=Theme.TEXT_MUTED,
        ).pack(anchor="w")

        sep = ctk.CTkFrame(sidebar, fg_color=Theme.BORDER, height=1)
        sep.pack(fill="x", padx=Theme.PAD_MD, pady=Theme.PAD_MD)

        for item in Theme.NAV_ITEMS:
            nav_id = item["id"]
            btn = NavButton(
                sidebar,
                icon=item["icon"],
                label=item["label"],
                command=lambda nid=nav_id: self.navigate(nid),
            )
            btn.pack(fill="x", padx=Theme.PAD_SM, pady=2)
            self._nav_buttons[nav_id] = btn

        spacer = ctk.CTkFrame(sidebar, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        status_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        status_frame.pack(fill="x", padx=Theme.PAD_MD, pady=Theme.PAD_SM)

        connected = self._sync.is_connected
        dot = "🟢" if connected else "🔴"
        text = "Sheets conectado" if connected else "Offline"
        color = Theme.SUCCESS if connected else Theme.TEXT_MUTED

        self._connection_label = ctk.CTkLabel(
            status_frame, text=f"  {dot}  {text}",
            font=Theme.FONT_TINY, text_color=color,
        )
        self._connection_label.pack(anchor="w")

        self._sync_btn = ctk.CTkButton(
            sidebar, text="🔄  Sincronizar",
            font=Theme.FONT_SMALL,
            fg_color="transparent",
            hover_color=Theme.BG_HOVER,
            text_color=Theme.TEXT_SECONDARY,
            border_width=1, border_color=Theme.BORDER,
            height=36,
            corner_radius=Theme.BUTTON_CORNER_RADIUS,
            command=self._sync_data,
        )
        self._sync_btn.pack(fill="x", padx=Theme.PAD_SM, pady=(Theme.PAD_SM, Theme.PAD_LG))

    def _build_content_area(self):
        self._content = ctk.CTkFrame(
            self, fg_color=Theme.BG_PRIMARY,
            corner_radius=0,
        )
        self._content.grid(row=0, column=1, sticky="nsew")

    def navigate(self, view_id: str):

        for nid, btn in self._nav_buttons.items():
            btn.set_active(nid == view_id)

        if self._current_view and self._current_view in self._views:
            self._views[self._current_view].pack_forget()

        if view_id not in self._views:
            self._views[view_id] = self._create_view(view_id)

        self._views[view_id].pack(fill="both", expand=True)
        self._current_view = view_id

        view = self._views[view_id]
        if hasattr(view, "refresh"):
            view.refresh()

    def _create_view(self, view_id: str) -> ctk.CTkFrame:
        views_map = {
            "dashboard": lambda: DashboardView(
                self._content, self._sync, app_ref=self
            ),
            "add": lambda: AddTransactionView(
                self._content, self._sync, app_ref=self
            ),
            "transactions": lambda: TransactionsView(
                self._content, self._sync, app_ref=self
            ),
            "reports": lambda: ReportsView(
                self._content, self._sync, app_ref=self
            ),
            "advisor": lambda: AdvisorView(
                self._content, self._sync, app_ref=self
            ),
            "technician": lambda: TechnicianView(
                self._content, self._sync, app_ref=self
            ),
            "pierre": lambda: PierreChatView(
                self._content, self._sync, app_ref=self
            ),
            "settings": lambda: SettingsView(
                self._content, self._sync, app_ref=self
            ),
        }

        factory = views_map.get(view_id)
        if factory:
            return factory()

        frame = ctk.CTkFrame(self._content, fg_color="transparent")
        ctk.CTkLabel(
            frame, text=f"View '{view_id}' não encontrada",
            font=Theme.FONT_HEADING, text_color=Theme.TEXT_MUTED,
        ).pack(expand=True)
        return frame

    def _sync_data(self):
        if not self._sync.is_connected:
            Toast(self, "Sem conexão com Google Sheets. Configure nas Configurações.", "warning")
            return

        self._sync_btn.configure(text="⏳  Sincronizando...", state="disabled")
        Toast(self, "Sincronizando com Google Sheets...", "info", duration=2000)

        def _on_done(df):
            self.after(0, lambda: (
                self._sync_btn.configure(text="🔄  Sincronizar", state="normal"),
                Toast(self, f"Sincronizado! {len(df)} transações carregadas.", "success"),
                self._refresh_current_view(),
            ))

        self._sync.pull_async(callback=_on_done)

    def _on_data_loaded(self):
        df = self._sync.dataframe
        Toast(self, f"Dados carregados: {len(df)} transações", "success")
        self._refresh_current_view()

    def _refresh_current_view(self):
        if self._current_view and self._current_view in self._views:
            view = self._views[self._current_view]
            if hasattr(view, "refresh"):
                view.refresh()

    def refresh_dashboard(self):
        if "dashboard" in self._views:
            self._views["dashboard"].refresh()

    def update_connection_status(self, connected: bool):
        dot = "🟢" if connected else "🔴"
        text = "Sheets conectado" if connected else "Offline"
        color = Theme.SUCCESS if connected else Theme.TEXT_MUTED
        self._connection_label.configure(text=f"  {dot}  {text}", text_color=color)
