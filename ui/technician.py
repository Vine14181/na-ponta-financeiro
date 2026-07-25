from ui.chat_base import ChatView
from technician import ask_technician

class TechnicianView(ChatView):
    TITLE = "🛠️ Técnico"
    SUBTITLE = ("Ensine como seus dados devem ser tratados. O Técnico guarda na memória e "
                "aplica no app — recategoriza transações, registra recorrências e fatos do seu perfil.")
    PLACEHOLDER = "Ensine algo ao Técnico..."
    WELCOME = (
        "Sou o Técnico — seu arquiteto de dados. Me diga como interpretar suas finanças "
        "e eu guardo e aplico automaticamente. Exemplos:\n\n"
        "•  \"Todo gasto no 'Mercado São Luiz' é Alimentação.\"\n"
        "•  \"O PIX de R$ 500 para a conta da corretora todo dia 5 é investimento.\"\n"
        "•  \"Considere que trabalho como autônomo e minha renda varia por mês.\"\n\n"
        "Pode falar naturalmente — eu transformo em regras."
    )

    def respond(self, question, history):
        resultado = ask_technician(self._sync, question, history=history)
        feitos = resultado.get("acoes_feitas") or []
        if feitos:
            resultado["extra"] = "✅ " + " • ".join(feitos)

            if self._app:
                try:
                    self._app.refresh_dashboard()
                except Exception:
                    pass
        return resultado
