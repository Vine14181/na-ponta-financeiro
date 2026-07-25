# Na Ponta

App de desktop para controle financeiro pessoal, com sincronização em Google
Sheets, importação via Open Finance (Pierre) e assistentes de IA.

> Projeto pessoal publicado para fins de avaliação/portfólio. O código está
> disponível para leitura; **não é licenciado para uso, cópia ou redistribuição**.
> Todos os direitos reservados.

## Requisitos

- Windows, Python 3.11+ (oficial, assinado)
- `pip install -r requirements.txt`

## Rodar

```
python main.py
```

## Sincronização com Google Sheets (gratuita, via Apps Script)

1. Crie uma planilha no Google Sheets → Extensões → Apps Script.
2. Cole o conteúdo de `apps_script.gs`. Gere um token com a função `gerarToken`
   (ou qualquer string aleatória longa) e defina-o em `const TOKEN` — o mesmo
   valor vai no app. O repositório não inclui nenhum token; cada pessoa cria o seu.
3. Rode a função `configurar` uma vez (autorize com sua conta).
4. Implante como App da Web (executar como você; acesso: qualquer pessoa) e copie a URL `/exec`.
5. No app, em Configurações, informe a URL. O token do app precisa ser igual ao do script.

## Chaves de API

As chaves (Pierre, IA) ficam num cofre local criptografado (Fernet + DPAPI no
Windows), fora de qualquer pasta sincronizada em nuvem. Configure-as na tela de
Configurações do app. Nada é enviado para fora dos serviços que você configurar.

## Segurança

- Saída de rede restrita a uma allowlist de hosts (`netguard.py`).
- Sanitização anti-injeção de fórmula ao escrever na planilha.
- Segredos redigidos de logs/mensagens de erro.
- Sem chaves no código; use `.env` (veja `.env.example`) ou o cofre.
