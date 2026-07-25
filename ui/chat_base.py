import re
import threading

import customtkinter as ctk

from ui.theme import Theme
from ui.widgets import Toast
from ai_client import AIClient

class ChatView(ctk.CTkFrame):

    TITLE = "Chat"
    SUBTITLE = ""
    PLACEHOLDER = "Digite sua mensagem..."
    WELCOME = "Olá!"
    ACTION_LABEL = None
    HISTORY_TURNS = 10

    def __init__(self, master, sync_manager, app_ref=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._sync = sync_manager
        self._app = app_ref
        self._history: list[tuple[str, str]] = []
        self._busy = False
        self._build_ui()

    def respond(self, question: str, history: list[tuple[str, str]]) -> dict:
        raise NotImplementedError

    def on_action(self):
        pass

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=Theme.PAD_MD, pady=(Theme.PAD_MD, 0))

        ctk.CTkLabel(
            header, text=self.TITLE,
            font=Theme.FONT_TITLE, text_color=Theme.TEXT_PRIMARY,
        ).pack(side="left")

        if self.ACTION_LABEL:
            self._action_btn = ctk.CTkButton(
                header, text=self.ACTION_LABEL,
                font=Theme.FONT_SMALL,
                fg_color=Theme.ACCENT, hover_color=Theme.ACCENT_HOVER,
                text_color="#FFFFFF", height=32, width=180, corner_radius=6,
                command=self._on_action_click,
            )
            self._action_btn.pack(side="right")
        else:
            self._action_btn = None

        if self.SUBTITLE:
            ctk.CTkLabel(
                self, text=self.SUBTITLE,
                font=Theme.FONT_TINY, text_color=Theme.TEXT_MUTED,
                wraplength=900, justify="left",
            ).pack(anchor="w", padx=Theme.PAD_MD, pady=(2, Theme.PAD_SM))

        self._chat = ctk.CTkScrollableFrame(
            self, fg_color=Theme.BG_SECONDARY,
            corner_radius=Theme.CARD_CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER,
            scrollbar_button_color=Theme.BORDER,
            scrollbar_button_hover_color=Theme.TEXT_MUTED,
        )
        self._chat.pack(fill="both", expand=True, padx=Theme.PAD_MD, pady=Theme.PAD_SM)

        self._add_bubble(self.WELCOME, from_user=False)

        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x", padx=Theme.PAD_MD, pady=(0, Theme.PAD_MD))

        self._entry = ctk.CTkEntry(
            input_frame,
            placeholder_text=self.PLACEHOLDER,
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_TERTIARY, border_color=Theme.BORDER,
            text_color=Theme.TEXT_PRIMARY,
            placeholder_text_color=Theme.TEXT_MUTED,
            height=44,
        )
        self._entry.pack(side="left", fill="x", expand=True, padx=(0, Theme.PAD_SM))
        self._entry.bind("<Return>", lambda _e: self._send())

        self._send_btn = ctk.CTkButton(
            input_frame, text="Enviar  ➤",
            font=Theme.FONT_BODY,
            fg_color=Theme.SUCCESS, hover_color="#2EA043",
            text_color="#FFFFFF", height=44, width=110,
            corner_radius=Theme.BUTTON_CORNER_RADIUS,
            command=self._send,
        )
        self._send_btn.pack(side="right")

    def _add_bubble(self, text: str, from_user: bool) -> ctk.CTkFrame:
        row = ctk.CTkFrame(self._chat, fg_color="transparent")
        row.pack(fill="x", padx=Theme.PAD_SM, pady=4)

        bubble = ctk.CTkFrame(
            row,
            fg_color=Theme.ACCENT if from_user else Theme.BG_TERTIARY,
            corner_radius=12,
        )
        bubble.pack(side="right" if from_user else "left", anchor="e" if from_user else "w")

        ctk.CTkLabel(
            bubble, text=text,
            font=Theme.FONT_BODY,
            text_color="#FFFFFF" if from_user else Theme.TEXT_PRIMARY,
            wraplength=680, justify="left", anchor="w",
        ).pack(padx=14, pady=10)

        self.after(50, self._scroll_to_bottom)
        return row

    def _scroll_to_bottom(self):
        try:
            self._chat._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

    @staticmethod
    def _clean_markdown(text: str) -> str:
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"^#{1,6}\s*", "", text, flags=re.M)
        text = re.sub(r"^\s*[\*\-]\s+", "•  ", text, flags=re.M)
        return text.strip()

    def _check_ready(self) -> bool:
        if self._busy:
            return False
        if not AIClient().is_configured:
            Toast(
                self.winfo_toplevel(),
                "Adicione sua chave de IA em Configurações → API Personalizada 1",
                "warning"
            )
            return False
        return True

    def _on_action_click(self):
        if not self._check_ready():
            return
        self.on_action()

    def _send(self):
        pergunta = self._entry.get().strip()
        if not pergunta or not self._check_ready():
            return
        self._entry.delete(0, "end")
        self._add_bubble(pergunta, from_user=True)
        self.dispatch(pergunta)

    def dispatch(self, pergunta: str):
        self._busy = True
        self._send_btn.configure(state="disabled")
        if self._action_btn:
            self._action_btn.configure(state="disabled")
        pensando = self._add_bubble("⏳ Pensando...", from_user=False)

        history = list(self._history[-self.HISTORY_TURNS:])

        def _worker():
            try:
                resultado = self.respond(pergunta, history)
            except Exception as e:
                resultado = {"erro": str(e)}
            try:
                self.after(0, lambda: self._on_answer(pensando, pergunta, resultado))
            except RuntimeError:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def _on_answer(self, pensando, pergunta: str, resultado: dict):
        try:
            pensando.destroy()
        except Exception:
            pass
        self._busy = False
        try:
            self._send_btn.configure(state="normal")
            if self._action_btn:
                self._action_btn.configure(state="normal")
        except Exception:
            return

        if "erro" in resultado:
            erro = str(resultado["erro"])
            baixo = erro.lower()
            if ("cota" in baixo or "crédito" in baixo or "credit" in baixo) and "todas as chaves" in baixo:
                msg = ("⚠️ Suas chaves de IA estão sem saldo no momento (cota do Gemini "
                       "esgotada e/ou sem créditos na Anthropic). A cota gratuita do Gemini "
                       "costuma voltar em algumas horas; para o Claude, adicione créditos em "
                       "console.anthropic.com. É só tentar de novo mais tarde.")
            else:
                msg = f"⚠️ Não consegui responder: {erro}"
            self._add_bubble(msg, from_user=False)
            return

        texto = self._clean_markdown(resultado.get("texto", ""))
        extra = resultado.get("extra")
        if extra:
            texto = f"{texto}\n\n— {extra}" if texto else extra
        self._add_bubble(texto or "(sem resposta)", from_user=False)

        self._history.append(("user", pergunta))
        self._history.append(("model", resultado.get("texto", "")))
        self._history = self._history[-(self.HISTORY_TURNS + 2):]

        if resultado.get("chave_usada") == "custom_api_2":
            Toast(
                self.winfo_toplevel(),
                "Chave principal indisponível — usei a reserva 🗝️",
                "info"
            )

    def refresh(self):
        pass
