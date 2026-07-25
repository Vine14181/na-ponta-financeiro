const TOKEN = "";

function gerarToken() {
  const t = Utilities.getUuid().replace(/-/g, "") + Utilities.getUuid().replace(/-/g, "");
  Logger.log("Gere/atualize aqui: cole este valor em TOKEN e no app (Configuracoes): " + t);
  return t;
}

const ABA_TRANSACOES = "Transações";
const ABA_CATEGORIAS = "Categorias";
const ABA_RESUMO = "Resumo Mensal";
const ABA_METAS = "Metas";

const CABECALHOS = [
  "ID", "Data", "Tipo", "Categoria", "Subcategoria",
  "Descrição", "Valor", "Método Pagamento", "Status",
  "Observações", "Mês", "Ano", "Atualizado"
];

const CATEGORIAS_DESPESA = {
  "🏠 Moradia": ["Aluguel", "Condomínio", "IPTU", "Manutenção"],
  "🍽️ Alimentação": ["Supermercado", "Restaurantes", "Delivery", "Lanches"],
  "🚗 Transporte": ["Combustível", "Uber/Táxi", "Estacionamento", "Manutenção Veículo", "Transporte Público"],
  "💊 Saúde": ["Plano de Saúde", "Farmácia", "Consultas", "Academia"],
  "📚 Educação": ["Mensalidade", "Livros", "Cursos"],
  "👕 Vestuário": ["Roupas", "Calçados", "Acessórios"],
  "🎮 Lazer": ["Streaming", "Jogos", "Viagens", "Hobbies"],
  "💡 Contas": ["Luz", "Água", "Gás", "Internet", "Telefone"],
  "🐕 Pets": ["Ração", "Veterinário", "Petshop"],
  "💇 Pessoal": ["Cabeleireiro", "Cosméticos", "Cuidados"],
  "📦 Compras": ["Eletrônicos", "Casa", "Presentes"],
  "💳 Financeiro": ["Juros", "Multas", "Taxas Bancárias", "Seguros"],
  "📌 Outros": ["Outros"],
};

const CATEGORIAS_RECEITA = {
  "💰 Salário": ["Salário Principal", "13º", "Férias"],
  "💼 Freelance": ["Projetos", "Consultoria"],
  "📈 Investimentos": ["Dividendos", "Rendimentos", "Juros"],
  "🎁 Presentes": ["Bonificações", "Presentes"],
  "💵 Vendas": ["Vendas"],
  "📌 Outras Receitas": ["Outras"],
};

const METODOS_PAGAMENTO = ["Pix", "Cartão Crédito", "Cartão Débito", "Dinheiro", "Boleto", "Transferência"];
const STATUS_TRANSACAO = ["Pago", "Pendente", "Atrasado"];
const MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
               "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"];

function configurar() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  let tx = ss.getSheetByName(ABA_TRANSACOES);
  if (!tx) tx = ss.insertSheet(ABA_TRANSACOES);
  tx.getRange(1, 1, 1, CABECALHOS.length).setValues([CABECALHOS])
    .setBackground("#0D1221").setFontColor("#F0F5FC")
    .setFontWeight("bold").setHorizontalAlignment("center");
  tx.getRange(2, 1, 1000, CABECALHOS.length).setNumberFormat("@");

  let cat = ss.getSheetByName(ABA_CATEGORIAS);
  if (!cat) cat = ss.insertSheet(ABA_CATEGORIAS);
  cat.clearContents();
  cat.getRange(1, 1, 1, 4).setValues([["CATEGORIAS DE DESPESA", "Subcategorias", "", "CATEGORIAS DE RECEITA"]]);

  let linha = 2;
  for (const [categoria, subs] of Object.entries(CATEGORIAS_DESPESA)) {
    cat.getRange(linha, 1, 1, 2).setValues([[categoria, subs.join(", ")]]);
    linha++;
  }
  let linhaReceita = 2;
  for (const [categoria, subs] of Object.entries(CATEGORIAS_RECEITA)) {
    cat.getRange(linhaReceita, 4, 1, 2).setValues([[categoria, subs.join(", ")]]);
    linhaReceita++;
  }
  cat.getRange(linha + 1, 1).setValue("MÉTODOS DE PAGAMENTO");
  METODOS_PAGAMENTO.forEach((m, i) => cat.getRange(linha + 2 + i, 1).setValue(m));
  cat.getRange(linhaReceita + 1, 4).setValue("STATUS");
  STATUS_TRANSACAO.forEach((s, i) => cat.getRange(linhaReceita + 2 + i, 4).setValue(s));

  let resumo = ss.getSheetByName(ABA_RESUMO);
  if (!resumo) resumo = ss.insertSheet(ABA_RESUMO);
  resumo.clearContents();
  resumo.getRange(1, 1, 1, 6)
    .setValues([["Mês", "Ano", "Receitas", "Despesas", "Saldo", "% Economia"]])
    .setBackground("#0D1221").setFontColor("#F0F5FC")
    .setFontWeight("bold").setHorizontalAlignment("center");

  const ano = new Date().getFullYear();
  MESES.forEach((mes, i) => {
    const l = i + 2;
    resumo.getRange(l, 1, 1, 6).setValues([[
      mes,
      String(ano),
      `=SUMIFS('${ABA_TRANSACOES}'!G:G,'${ABA_TRANSACOES}'!C:C,"Receita",'${ABA_TRANSACOES}'!K:K,A${l},'${ABA_TRANSACOES}'!L:L,B${l})`,
      `=SUMIFS('${ABA_TRANSACOES}'!G:G,'${ABA_TRANSACOES}'!C:C,"Despesa",'${ABA_TRANSACOES}'!K:K,A${l},'${ABA_TRANSACOES}'!L:L,B${l})`,
      `=C${l}-D${l}`,
      `=IF(C${l}>0,(C${l}-D${l})/C${l}*100,0)`,
    ]]);
  });

  let metas = ss.getSheetByName(ABA_METAS);
  if (!metas) metas = ss.insertSheet(ABA_METAS);
  metas.clearContents();
  metas.getRange(1, 1, 1, 5)
    .setValues([["Meta", "Valor Alvo", "Valor Atual", "Prazo", "% Conclusão"]])
    .setBackground("#0D1221").setFontColor("#F0F5FC")
    .setFontWeight("bold").setHorizontalAlignment("center");
  metas.getRange(2, 1, 1, 5).setValues([["Reserva de Emergência", "10000", "0", "31/12/2026", "=C2/B2*100"]]);

  try {
    SpreadsheetApp.getUi().alert("Planilha configurada.");
  } catch (err) {
    Logger.log("Planilha configurada.");
  }
}

function resposta_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function abaTransacoes_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(ABA_TRANSACOES);
  if (!sh) {
    sh = ss.insertSheet(ABA_TRANSACOES);
    sh.getRange(1, 1, 1, CABECALHOS.length).setValues([CABECALHOS]);
  }
  return sh;
}

function doGet(e) {
  if (!TOKEN) {
    return resposta_({ ok: false, error: "token_nao_configurado" });
  }
  if (!e || !e.parameter || e.parameter.token !== TOKEN) {
    return resposta_({ ok: false, error: "unauthorized" });
  }
  const sh = abaTransacoes_();
  const valores = sh.getDataRange().getDisplayValues();
  return resposta_({
    ok: true,
    headers: valores.length ? valores[0] : CABECALHOS,
    rows: valores.slice(1).filter(r => r.some(c => c !== "")),
  });
}

function doPost(e) {
  let corpo;
  try {
    corpo = JSON.parse(e.postData.contents);
  } catch (err) {
    return resposta_({ ok: false, error: "bad_json" });
  }
  if (!TOKEN || corpo.token !== TOKEN) {
    return resposta_({ ok: false, error: "unauthorized" });
  }

  const sh = abaTransacoes_();
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    if (corpo.action === "append") {
      sh.appendRow(corpo.row.map(String));
      return resposta_({ ok: true });
    }
    if (corpo.action === "replace") {
      sh.clearContents();
      sh.getRange(1, 1, 1, CABECALHOS.length).setValues([CABECALHOS]);
      const linhas = (corpo.rows || []).map(r => r.map(String));
      if (linhas.length) {
        sh.getRange(2, 1, linhas.length, CABECALHOS.length).setValues(linhas);
      }
      return resposta_({ ok: true });
    }
    return resposta_({ ok: false, error: "unknown_action" });
  } finally {
    lock.releaseLock();
  }
}
