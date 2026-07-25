import os
import customtkinter as ctk
from tkinter import filedialog

from ui.theme import Theme
from ui.widgets import SectionHeader, Toast
from key_vault import KeyVault
from config import CREDENTIALS_PATH, SETTINGS_FILE, load_settings, update_setting

class SettingsView(ctk.CTkFrame):

    def __init__(self, master, sync_manager, app_ref=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._sync = sync_manager
        self._app = app_ref
        self._vault = KeyVault()

        self._build_ui()

    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=Theme.BORDER,
            scrollbar_button_hover_color=Theme.TEXT_MUTED,
        )
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(
            scroll, text="Configurações",
            font=Theme.FONT_TITLE, text_color=Theme.TEXT_PRIMARY,
        ).pack(anchor="w", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_SM))

        ctk.CTkLabel(
            scroll, text="Gerencie integrações, chaves de API e preferências",
            font=Theme.FONT_BODY, text_color=Theme.TEXT_SECONDARY,
        ).pack(anchor="w", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))

        SectionHeader(scroll, title="🔗 Google Sheets").pack(
            fill="x", padx=Theme.PAD_MD, pady=Theme.PAD_SM
        )

        sheets_card = ctk.CTkFrame(
            scroll, fg_color=Theme.BG_SECONDARY,
            corner_radius=Theme.CARD_CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER,
        )
        sheets_card.pack(fill="x", padx=Theme.PAD_MD, pady=Theme.PAD_SM)

        sheets_inner = ctk.CTkFrame(sheets_card, fg_color="transparent")
        sheets_inner.pack(fill="x", padx=Theme.PAD_LG, pady=Theme.PAD_MD)

        self._sheets_status_frame = ctk.CTkFrame(sheets_inner, fg_color="transparent")
        self._sheets_status_frame.pack(fill="x", pady=Theme.PAD_SM)

        connected = self._sync.is_connected
        status_icon = "🟢" if connected else "🔴"
        status_text = "Conectado ao Google Sheets" if connected else "Desconectado"
        status_color = Theme.SUCCESS if connected else Theme.DANGER

        connected_via = ""
        if connected and getattr(self._sync, "backend", None) == "apps_script":
            connected_via = " (via Apps Script)"
        elif connected and getattr(self._sync, "backend", None) == "gspread":
            connected_via = " (via Service Account)"

        self._sheets_status = ctk.CTkLabel(
            self._sheets_status_frame,
            text=f"  {status_icon}  {status_text}{connected_via}",
            font=Theme.FONT_BODY, text_color=status_color,
        )
        self._sheets_status.pack(side="left")

        as_frame = ctk.CTkFrame(sheets_inner, fg_color="transparent")
        as_frame.pack(fill="x", pady=Theme.PAD_SM)

        ctk.CTkLabel(
            as_frame, text="URL do Apps Script (recomendado — veja apps_script.gs)",
            font=Theme.FONT_SMALL, text_color=Theme.TEXT_SECONDARY,
        ).pack(anchor="w")

        as_input_frame = ctk.CTkFrame(as_frame, fg_color="transparent")
        as_input_frame.pack(fill="x", pady=(4, 0))

        saved_url = load_settings().get("apps_script_url", "")

        self._as_url_entry = ctk.CTkEntry(
            as_input_frame,
            placeholder_text="https://script.google.com/macros/s/.../exec",
            font=Theme.FONT_SMALL,
            fg_color=Theme.BG_TERTIARY,
            border_color=Theme.BORDER,
            text_color=Theme.TEXT_PRIMARY,
            placeholder_text_color=Theme.TEXT_MUTED,
            height=Theme.INPUT_HEIGHT,
        )
        self._as_url_entry.pack(side="left", fill="x", expand=True, padx=(0, Theme.PAD_SM))
        if saved_url:
            self._as_url_entry.insert(0, saved_url)

        ctk.CTkButton(
            as_input_frame, text="💾 Salvar",
            font=Theme.FONT_SMALL,
            fg_color=Theme.SUCCESS,
            hover_color="#2EA043",
            text_color="#FFFFFF",
            height=Theme.INPUT_HEIGHT, width=90,
            corner_radius=6,
            command=self._save_apps_script_url,
        ).pack(side="right")

        cred_frame = ctk.CTkFrame(sheets_inner, fg_color="transparent")
        cred_frame.pack(fill="x", pady=Theme.PAD_SM)

        ctk.CTkLabel(
            cred_frame, text="Arquivo de Credenciais (credentials.json) — alternativa avançada",
            font=Theme.FONT_SMALL, text_color=Theme.TEXT_SECONDARY,
        ).pack(anchor="w")

        cred_input_frame = ctk.CTkFrame(cred_frame, fg_color="transparent")
        cred_input_frame.pack(fill="x", pady=(4, 0))

        has_creds = os.path.exists(CREDENTIALS_PATH)
        cred_text = CREDENTIALS_PATH if has_creds else "Nenhum arquivo selecionado"

        self._cred_label = ctk.CTkLabel(
            cred_input_frame, text=cred_text,
            font=Theme.FONT_SMALL,
            text_color=Theme.SUCCESS if has_creds else Theme.TEXT_MUTED,
            anchor="w",
        )
        self._cred_label.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            cred_input_frame, text="📂 Selecionar",
            font=Theme.FONT_SMALL,
            fg_color=Theme.ACCENT,
            hover_color=Theme.ACCENT_HOVER,
            text_color="#FFFFFF",
            height=32, width=100,
            corner_radius=6,
            command=self._select_credentials,
        ).pack(side="right")

        ctk.CTkButton(
            sheets_inner, text="🔄  Reconectar ao Google Sheets",
            font=Theme.FONT_BODY,
            fg_color="transparent",
            hover_color=Theme.BG_HOVER,
            text_color=Theme.ACCENT,
            border_width=1, border_color=Theme.BORDER,
            height=40, corner_radius=Theme.BUTTON_CORNER_RADIUS,
            command=self._reconnect_sheets,
        ).pack(fill="x", pady=Theme.PAD_SM)

        SectionHeader(scroll, title="🔐 Cofre de API Keys").pack(
            fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_SM)
        )

        ctk.CTkLabel(
            scroll,
            text="As chaves são criptografadas localmente com AES-128. Nunca ficam em texto puro.",
            font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED,
        ).pack(anchor="w", padx=Theme.PAD_MD, pady=(0, Theme.PAD_SM))

        self._build_key_field(
            scroll,
            key_name="pierre",
            display_name="Pierre (CloudWalk)",
            description="Chave de API do Pierre Finance para integração com Open Finance",
            icon="🏦",
        )

        self._build_key_field(
            scroll,
            key_name="custom_api",
            display_name="API Personalizada 1",
            description="Chave principal do Conselheiro — Claude (sk-ant-...) ou Gemini (AIza...), detectado automaticamente",
            icon="🔑",
        )

        self._build_key_field(
            scroll,
            key_name="custom_api_2",
            display_name="API Personalizada 2",
            description="Chave reserva — usada automaticamente se a principal falhar ou ficar sem tokens",
            icon="🗝️",
        )

        SectionHeader(scroll, title="⚙️ Preferências").pack(
            fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, Theme.PAD_SM)
        )

        prefs_card = ctk.CTkFrame(
            scroll, fg_color=Theme.BG_SECONDARY,
            corner_radius=Theme.CARD_CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER,
        )
        prefs_card.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_SM, Theme.PAD_MD))

        prefs_inner = ctk.CTkFrame(prefs_card, fg_color="transparent")
        prefs_inner.pack(fill="x", padx=Theme.PAD_LG, pady=Theme.PAD_MD)

        currency_frame = ctk.CTkFrame(prefs_inner, fg_color="transparent")
        currency_frame.pack(fill="x", pady=Theme.PAD_SM)

        ctk.CTkLabel(
            currency_frame, text="Moeda", font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_SECONDARY,
        ).pack(anchor="w")

        self._currency_var = ctk.StringVar(value="BRL (R$)")
        ctk.CTkComboBox(
            currency_frame,
            values=["BRL (R$)", "USD ($)", "EUR (€)"],
            variable=self._currency_var,
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_TERTIARY,
            border_color=Theme.BORDER,
            button_color=Theme.ACCENT,
            dropdown_fg_color=Theme.BG_SECONDARY,
            text_color=Theme.TEXT_PRIMARY,
            dropdown_text_color=Theme.TEXT_PRIMARY,
            height=Theme.INPUT_HEIGHT,
            state="readonly",
        ).pack(fill="x", pady=(4, 0))

        theme_frame = ctk.CTkFrame(prefs_inner, fg_color="transparent")
        theme_frame.pack(fill="x", pady=Theme.PAD_SM)

        ctk.CTkLabel(
            theme_frame, text="Tema", font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_SECONDARY,
        ).pack(anchor="w")

        self._theme_var = ctk.StringVar(value="Dark")
        ctk.CTkSegmentedButton(
            theme_frame,
            values=["Dark", "Light"],
            variable=self._theme_var,
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_TERTIARY,
            selected_color=Theme.ACCENT,
            selected_hover_color=Theme.ACCENT_HOVER,
            unselected_color=Theme.BG_TERTIARY,
            text_color=Theme.TEXT_PRIMARY,
        ).pack(fill="x", pady=(4, 0))

        ctk.CTkLabel(
            scroll, text="Na Ponta v1.0.0  •  Feito com 💙",
            font=Theme.FONT_TINY, text_color=Theme.TEXT_MUTED,
        ).pack(pady=(Theme.PAD_MD, Theme.PAD_LG))

    def _build_key_field(self, parent, key_name: str, display_name: str,
                         description: str, icon: str):
        card = ctk.CTkFrame(
            parent, fg_color=Theme.BG_SECONDARY,
            corner_radius=Theme.CARD_CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER,
        )
        card.pack(fill="x", padx=Theme.PAD_MD, pady=Theme.PAD_SM)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=Theme.PAD_LG, pady=Theme.PAD_MD)

        header_frame = ctk.CTkFrame(inner, fg_color="transparent")
        header_frame.pack(fill="x")

        has_key = self._vault.has_key(key_name)
        status_icon = "🟢" if has_key else "🔴"
        status_text = "Configurada" if has_key else "Não configurada"
        status_color = Theme.SUCCESS if has_key else Theme.TEXT_MUTED

        ctk.CTkLabel(
            header_frame, text=f"  {icon}  {display_name}",
            font=Theme.FONT_HEADING, text_color=Theme.TEXT_PRIMARY,
        ).pack(side="left")

        status_label = ctk.CTkLabel(
            header_frame, text=f"  {status_icon} {status_text}",
            font=Theme.FONT_SMALL, text_color=status_color,
        )
        status_label.pack(side="right")

        ctk.CTkLabel(
            inner, text=description,
            font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED,
        ).pack(anchor="w", pady=(2, Theme.PAD_SM))

        if has_key:
            masked = self._vault.mask_key(key_name)
            ctk.CTkLabel(
                inner, text=f"Chave: {masked}",
                font=Theme.FONT_MONO, text_color=Theme.TEXT_SECONDARY,
            ).pack(anchor="w", pady=(0, Theme.PAD_SM))

        input_frame = ctk.CTkFrame(inner, fg_color="transparent")
        input_frame.pack(fill="x", pady=Theme.PAD_XS)

        key_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Cole sua API key aqui...",
            font=Theme.FONT_MONO,
            fg_color=Theme.BG_TERTIARY,
            border_color=Theme.BORDER,
            text_color=Theme.TEXT_PRIMARY,
            placeholder_text_color=Theme.TEXT_MUTED,
            height=Theme.INPUT_HEIGHT,
            show="●",
        )
        key_entry.pack(side="left", fill="x", expand=True, padx=(0, Theme.PAD_SM))

        ctk.CTkButton(
            input_frame, text="💾 Salvar",
            font=Theme.FONT_SMALL,
            fg_color=Theme.SUCCESS,
            hover_color="#2EA043",
            text_color="#FFFFFF",
            height=Theme.INPUT_HEIGHT, width=90,
            corner_radius=6,
            command=lambda: self._save_key(key_name, key_entry, display_name),
        ).pack(side="left", padx=(0, Theme.PAD_XS))

        if has_key:
            ctk.CTkButton(
                input_frame, text="🗑️",
                font=Theme.FONT_SMALL,
                fg_color=Theme.DANGER_DIM,
                hover_color=Theme.DANGER,
                text_color=Theme.DANGER,
                height=Theme.INPUT_HEIGHT, width=40,
                corner_radius=6,
                command=lambda: self._delete_key(key_name, display_name),
            ).pack(side="left")

    def _save_key(self, key_name: str, entry: ctk.CTkEntry, display_name: str):
        value = entry.get().strip()
        if not value:
            Toast(self.winfo_toplevel(), "Digite uma chave para salvar!", "warning")
            return

        self._vault.save_key(key_name, value)
        entry.delete(0, "end")
        Toast(
            self.winfo_toplevel(),
            f"Chave {display_name} salva com segurança! 🔒",
            "success"
        )

        self._rebuild()

    def _delete_key(self, key_name: str, display_name: str):
        self._vault.delete_key(key_name)
        Toast(
            self.winfo_toplevel(),
            f"Chave {display_name} removida!",
            "info"
        )
        self._rebuild()

    def _save_apps_script_url(self):
        url = self._as_url_entry.get().strip()
        if not url:
            Toast(self.winfo_toplevel(), "Cole a URL do Apps Script primeiro!", "warning")
            return
        if "/exec" not in url:
            Toast(
                self.winfo_toplevel(),
                "URL inválida — ela deve terminar em /exec",
                "warning"
            )
            return

        update_setting("apps_script_url", url)
        Toast(self.winfo_toplevel(), "URL salva! Conectando...", "success")
        self._reconnect_sheets()

    def _select_credentials(self):
        filepath = filedialog.askopenfilename(
            title="Selecionar credentials.json",
            filetypes=[("JSON files", "*.json")],
        )
        if filepath:

            import shutil
            try:
                shutil.copy2(filepath, CREDENTIALS_PATH)
                self._cred_label.configure(
                    text=CREDENTIALS_PATH,
                    text_color=Theme.SUCCESS,
                )
                Toast(
                    self.winfo_toplevel(),
                    "Credenciais salvas! Clique em Reconectar.",
                    "success"
                )
            except Exception as e:
                Toast(
                    self.winfo_toplevel(),
                    f"Erro ao copiar: {e}",
                    "error"
                )

    def _reconnect_sheets(self):
        Toast(self.winfo_toplevel(), "Reconectando...", "info", duration=1500)

        def _on_connect(success):
            if success:
                self.after(0, lambda: Toast(
                    self.winfo_toplevel(),
                    "Conectado ao Google Sheets! ✅",
                    "success"
                ))
                self.after(0, self._rebuild)

                self._sync.pull_async(
                    callback=lambda _: self.after(0, lambda: (
                        self._app.refresh_dashboard() if self._app else None
                    ))
                )
            else:
                self.after(0, lambda: Toast(
                    self.winfo_toplevel(),
                    "Falha ao conectar. Verifique as credenciais.",
                    "error"
                ))

        self._sync.connect_async(callback=_on_connect)

    def _rebuild(self):
        for child in self.winfo_children():
            child.destroy()
        self._build_ui()

    def refresh(self):
        self._rebuild()
