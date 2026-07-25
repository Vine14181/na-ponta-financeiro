from ui.chat_base import ChatView
from pierre_assistant import ask_pierre

class PierreChatView(ChatView):
    TITLE = "💬 Pierre"
    SUBTITLE = ("Converse sobre seu dinheiro em linguagem natural, com os dados reais das suas "
                "contas conectadas ao Pierre (Open Finance). Assistente do Na Ponta no estilo Pierre.")
    PLACEHOLDER = "Fale com o Pierre..."
    WELCOME = (
        "Oi! Eu sou o Pierre. Tô de olho nas suas contas conectadas. "
        "Pode me perguntar em linguagem normal, tipo:\n\n"
        "•  \"Quanto eu gastei esse mês?\"\n"
        "•  \"Como tá minha fatura do cartão?\"\n"
        "•  \"Tenho quanto no banco agora?\"\n"
        "•  \"Onde meu dinheiro mais foi embora?\""
    )

    def respond(self, question, history):
        return ask_pierre(question, history=history)
