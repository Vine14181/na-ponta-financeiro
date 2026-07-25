from ui.chat_base import ChatView
from advisor import ask_advisor, monthly_diagnosis

class AdvisorView(ChatView):
    TITLE = "🧭 Conselheiro"
    SUBTITLE = ("Análises com base nos seus dados reais. Um resumo deles é enviado à IA "
                "configurada em Configurações. Não substitui um assessor certificado.")
    PLACEHOLDER = "Pergunte sobre suas finanças..."
    ACTION_LABEL = "📋  Diagnóstico do mês"
    WELCOME = (
        "Olá! Sou seu conselheiro financeiro. Posso analisar seu mês, "
        "sugerir estratégias para dívidas e parcelas, e montar um plano de investimentos "
        "com base nos seus dados reais.\n\n"
        "Experimente o botão \"Diagnóstico do mês\" ou pergunte algo como:\n"
        "•  \"Devo parcelar uma compra de R$ 1.200 em quantas vezes?\"\n"
        "•  \"Qual dívida devo quitar primeiro?\"\n"
        "•  \"Quanto posso investir por mês?\""
    )

    def respond(self, question, history):
        return ask_advisor(self._sync, question, history=history)

    def on_action(self):
        self._add_bubble("📋 Diagnóstico completo do mês, por favor.", from_user=True)
        self.dispatch("__diagnostico__")

    def dispatch(self, pergunta):

        if pergunta == "__diagnostico__":
            self._busy = True
            self._send_btn.configure(state="disabled")
            if self._action_btn:
                self._action_btn.configure(state="disabled")
            pensando = self._add_bubble("⏳ Analisando seus dados...", from_user=False)
            import threading

            def _worker():
                try:
                    resultado = monthly_diagnosis(self._sync)
                except Exception as e:
                    resultado = {"erro": str(e)}
                try:
                    self.after(0, lambda: self._on_answer(pensando, "Diagnóstico do mês", resultado))
                except RuntimeError:
                    pass

            threading.Thread(target=_worker, daemon=True).start()
            return
        super().dispatch(pergunta)
