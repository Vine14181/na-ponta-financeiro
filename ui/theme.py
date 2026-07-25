class Theme:

    BG_PRIMARY = "#0D1117"
    BG_SECONDARY = "#161B22"
    BG_TERTIARY = "#1C2128"
    BG_HOVER = "#1F2937"

    ACCENT = "#58A6FF"
    ACCENT_HOVER = "#79C0FF"
    ACCENT_DIM = "#1F3A5F"

    SUCCESS = "#3FB950"
    SUCCESS_DIM = "#1A3A2A"
    DANGER = "#F85149"
    DANGER_DIM = "#3D1A1A"
    WARNING = "#D29922"
    WARNING_DIM = "#3D2E0A"
    PURPLE = "#BC8CFF"

    TEXT_PRIMARY = "#F0F6FC"
    TEXT_SECONDARY = "#8B949E"
    TEXT_MUTED = "#484F58"
    TEXT_LINK = "#58A6FF"

    BORDER = "#30363D"
    BORDER_LIGHT = "#21262D"

    FONT_FAMILY = "Segoe UI"
    FONT_FAMILY_MONO = "Cascadia Code"

    FONT_TITLE = (FONT_FAMILY, 24, "bold")
    FONT_SUBTITLE = (FONT_FAMILY, 18, "bold")
    FONT_HEADING = (FONT_FAMILY, 15, "bold")
    FONT_BODY = (FONT_FAMILY, 13)
    FONT_BODY_BOLD = (FONT_FAMILY, 13, "bold")
    FONT_SMALL = (FONT_FAMILY, 11)
    FONT_TINY = (FONT_FAMILY, 10)
    FONT_METRIC = (FONT_FAMILY, 28, "bold")
    FONT_METRIC_LABEL = (FONT_FAMILY, 11)
    FONT_MONO = (FONT_FAMILY_MONO, 12)

    PAD_XS = 4
    PAD_SM = 8
    PAD_MD = 16
    PAD_LG = 24
    PAD_XL = 32

    SIDEBAR_WIDTH = 220
    CARD_CORNER_RADIUS = 12
    BUTTON_CORNER_RADIUS = 8
    INPUT_HEIGHT = 38

    CHART_COLORS = [
        "#58A6FF",
        "#3FB950",
        "#F85149",
        "#D29922",
        "#BC8CFF",
        "#F778BA",
        "#79C0FF",
        "#56D364",
        "#FFA657",
        "#FF7B72",
        "#D2A8FF",
        "#A5D6FF",
        "#7EE787",
    ]

    NAV_ITEMS = [
        {"id": "dashboard",    "icon": "📊", "label": "Dashboard"},
        {"id": "add",          "icon": "➕", "label": "Nova Transação"},
        {"id": "transactions", "icon": "📋", "label": "Transações"},
        {"id": "reports",      "icon": "📈", "label": "Relatórios"},
        {"id": "advisor",      "icon": "🧭", "label": "Conselheiro"},
        {"id": "technician",   "icon": "🛠️", "label": "Técnico"},
        {"id": "pierre",       "icon": "💬", "label": "Pierre"},
        {"id": "settings",     "icon": "⚙️", "label": "Configurações"},
    ]

    @staticmethod
    def configure_matplotlib():
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        plt.rcParams.update({
            "figure.facecolor": Theme.BG_SECONDARY,
            "axes.facecolor": Theme.BG_SECONDARY,
            "axes.edgecolor": Theme.BORDER,
            "axes.labelcolor": Theme.TEXT_SECONDARY,
            "text.color": Theme.TEXT_PRIMARY,
            "xtick.color": Theme.TEXT_SECONDARY,
            "ytick.color": Theme.TEXT_SECONDARY,
            "grid.color": Theme.BORDER_LIGHT,
            "grid.alpha": 0.5,
            "legend.facecolor": Theme.BG_TERTIARY,
            "legend.edgecolor": Theme.BORDER,
            "font.family": "sans-serif",
            "font.sans-serif": [Theme.FONT_FAMILY],
            "font.size": 11,
        })
