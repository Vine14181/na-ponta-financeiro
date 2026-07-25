import customtkinter as ctk
from ui.theme import Theme

class MetricCard(ctk.CTkFrame):

    def __init__(self, master, icon: str, label: str, value: str,
                 color: str = Theme.ACCENT, **kwargs):
        super().__init__(
            master,
            fg_color=Theme.BG_SECONDARY,
            corner_radius=Theme.CARD_CORNER_RADIUS,
            border_width=1,
            border_color=Theme.BORDER,
            **kwargs
        )

        self._color = color

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=Theme.PAD_LG, pady=Theme.PAD_MD)

        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x", anchor="w")

        self._icon_label = ctk.CTkLabel(
            header, text=icon, font=(Theme.FONT_FAMILY, 20),
            text_color=color
        )
        self._icon_label.pack(side="left")

        self._label = ctk.CTkLabel(
            header, text=label, font=Theme.FONT_METRIC_LABEL,
            text_color=Theme.TEXT_SECONDARY
        )
        self._label.pack(side="left", padx=(Theme.PAD_SM, 0))

        self._value_label = ctk.CTkLabel(
            inner, text=value, font=Theme.FONT_METRIC,
            text_color=Theme.TEXT_PRIMARY, anchor="w"
        )
        self._value_label.pack(fill="x", pady=(Theme.PAD_SM, 0))

    def update_value(self, value: str, color: str = None):
        self._value_label.configure(text=value)
        if color:
            self._value_label.configure(text_color=color)

class StatusBadge(ctk.CTkLabel):

    STATUS_COLORS = {
        "Pago": (Theme.SUCCESS, Theme.SUCCESS_DIM),
        "Pendente": (Theme.WARNING, Theme.WARNING_DIM),
        "Atrasado": (Theme.DANGER, Theme.DANGER_DIM),
    }

    def __init__(self, master, status: str, **kwargs):
        fg, bg = self.STATUS_COLORS.get(status, (Theme.TEXT_SECONDARY, Theme.BG_TERTIARY))
        super().__init__(
            master,
            text=f"  {status}  ",
            font=Theme.FONT_TINY,
            text_color=fg,
            fg_color=bg,
            corner_radius=4,
            **kwargs
        )

class NavButton(ctk.CTkButton):

    def __init__(self, master, icon: str, label: str, is_active: bool = False,
                 command=None, **kwargs):
        self._is_active = is_active
        bg = Theme.ACCENT_DIM if is_active else "transparent"
        text_color = Theme.ACCENT if is_active else Theme.TEXT_SECONDARY

        super().__init__(
            master,
            text=f"  {icon}  {label}",
            font=Theme.FONT_BODY,
            fg_color=bg,
            text_color=text_color,
            hover_color=Theme.BG_HOVER,
            anchor="w",
            height=44,
            corner_radius=Theme.BUTTON_CORNER_RADIUS,
            command=command,
            **kwargs
        )

    def set_active(self, active: bool):
        self._is_active = active
        if active:
            self.configure(
                fg_color=Theme.ACCENT_DIM,
                text_color=Theme.ACCENT,
            )
        else:
            self.configure(
                fg_color="transparent",
                text_color=Theme.TEXT_SECONDARY,
            )

class SearchBar(ctk.CTkFrame):

    def __init__(self, master, placeholder: str = "Buscar...",
                 on_search=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._on_search = on_search

        self._entry = ctk.CTkEntry(
            self,
            placeholder_text=f"🔍  {placeholder}",
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_TERTIARY,
            border_color=Theme.BORDER,
            text_color=Theme.TEXT_PRIMARY,
            placeholder_text_color=Theme.TEXT_MUTED,
            height=Theme.INPUT_HEIGHT,
            corner_radius=Theme.BUTTON_CORNER_RADIUS,
        )
        self._entry.pack(fill="x", expand=True)

        if on_search:
            self._entry.bind("<Return>", lambda e: on_search(self._entry.get()))
            self._entry.bind("<KeyRelease>", lambda e: on_search(self._entry.get()))

    def get(self) -> str:
        return self._entry.get()

    def clear(self):
        self._entry.delete(0, "end")

class FilterDropdown(ctk.CTkFrame):

    def __init__(self, master, label: str, values: list[str],
                 on_change=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._label = ctk.CTkLabel(
            self, text=label, font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_SECONDARY
        )
        self._label.pack(anchor="w")

        self._var = ctk.StringVar(value="Todos")
        self._dropdown = ctk.CTkComboBox(
            self,
            values=["Todos"] + values,
            variable=self._var,
            font=Theme.FONT_SMALL,
            dropdown_font=Theme.FONT_SMALL,
            fg_color=Theme.BG_TERTIARY,
            border_color=Theme.BORDER,
            button_color=Theme.ACCENT,
            button_hover_color=Theme.ACCENT_HOVER,
            dropdown_fg_color=Theme.BG_SECONDARY,
            dropdown_hover_color=Theme.BG_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            dropdown_text_color=Theme.TEXT_PRIMARY,
            height=32,
            corner_radius=6,
            state="readonly",
            command=on_change,
        )
        self._dropdown.pack(fill="x", pady=(2, 0))

    def get(self) -> str:
        return self._var.get()

    def reset(self):
        self._var.set("Todos")

class SectionHeader(ctk.CTkFrame):

    def __init__(self, master, title: str, action_text: str = None,
                 action_command=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._title = ctk.CTkLabel(
            self, text=title, font=Theme.FONT_HEADING,
            text_color=Theme.TEXT_PRIMARY
        )
        self._title.pack(side="left")

        if action_text and action_command:
            self._action = ctk.CTkButton(
                self,
                text=action_text,
                font=Theme.FONT_SMALL,
                fg_color="transparent",
                text_color=Theme.ACCENT,
                hover_color=Theme.BG_HOVER,
                height=28,
                corner_radius=6,
                command=action_command,
            )
            self._action.pack(side="right")

class Toast(ctk.CTkFrame):

    def __init__(self, master, message: str,
                 toast_type: str = "info", duration: int = 3000):
        colors = {
            "info": (Theme.ACCENT, Theme.ACCENT_DIM),
            "success": (Theme.SUCCESS, Theme.SUCCESS_DIM),
            "error": (Theme.DANGER, Theme.DANGER_DIM),
            "warning": (Theme.WARNING, Theme.WARNING_DIM),
        }
        text_color, bg_color = colors.get(toast_type, colors["info"])

        super().__init__(
            master,
            fg_color=bg_color,
            corner_radius=8,
            border_width=1,
            border_color=text_color,
        )

        icons = {"info": "ℹ️", "success": "✅", "error": "❌", "warning": "⚠️"}
        icon = icons.get(toast_type, "ℹ️")

        label = ctk.CTkLabel(
            self,
            text=f"  {icon}  {message}  ",
            font=Theme.FONT_BODY,
            text_color=text_color,
        )
        label.pack(padx=Theme.PAD_MD, pady=Theme.PAD_SM)

        self.place(relx=0.98, rely=0.97, anchor="se")

        self.after(duration, self._fade_out)

    def _fade_out(self):
        try:
            self.destroy()
        except Exception:
            pass

class EmptyState(ctk.CTkFrame):

    def __init__(self, master, icon: str, title: str,
                 subtitle: str = "", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        ctk.CTkLabel(
            self, text=icon, font=(Theme.FONT_FAMILY, 48),
            text_color=Theme.TEXT_MUTED
        ).pack(pady=(Theme.PAD_XL, Theme.PAD_SM))

        ctk.CTkLabel(
            self, text=title, font=Theme.FONT_HEADING,
            text_color=Theme.TEXT_SECONDARY
        ).pack()

        if subtitle:
            ctk.CTkLabel(
                self, text=subtitle, font=Theme.FONT_SMALL,
                text_color=Theme.TEXT_MUTED
            ).pack(pady=(Theme.PAD_XS, 0))
