// --- FUNÇÃO PARA REMONTAGEM DO PAINEL TEXTUAL ESTÁTICO ---
function extrairMarkupFiltros() {
  return {
    inline_keyboard: [
      // --- SEÇÃO 1: BINGOS ---
      [{"text": "🎯 Escolha um bingo:", "callback_data": "ignore"}],
      [
        {"text": "Bingo 3", "callback_data": "cb_bingo_3"},
        {"text": "Bingo 5", "callback_data": "cb_bingo_5"},
        {"text": "Bingo 7", "callback_data": "cb_bingo_7"}
      ],
      // --- SEÇÃO 2: HORÁRIOS ---
      [{"text": "⏳ Escolha uma janela:", "callback_data": "ignore"}],
      [
        {"text": "Janela 3H", "callback_data": "cb_hora_3H"},
        {"text": "Janela 5H", "callback_data": "cb_hora_5H"},
        {"text": "Do Dia", "callback_data": "cb_hora_DIA"}
      ],
      // --- SEÇÃO 3: ESTRATÉGIA ---
      [{"text": "📊 Escolha um modo:", "callback_data": "ignore"}],
      [
        {"text": "Maiores Odds", "callback_data": "cb_tipo_ODDS"},
        {"text": "Mais acertos", "callback_data": "cb_tipo_ACERTOS"},
        {"text": "Equilibrado", "callback_data": "cb_tipo_AMBAS"}
      ],
      // --- BOTÃO DE DISPARO REAL DEFINITIVO ---
      [{"text": "🚀 GERAR BILHETE", "callback_data": "cb_acao_GERAR"}]
    ]
  };
}

export default {
  async fetch(request, env, ctx) {
    if (request.method === "POST") {
      try {
        const update = await request.json();

        let chatId = null;
        let userText = null;
        let callbackQueryId = null;

        // --- 1. DETECÇÃO DE ORIGEM ---
        if (update.callback_query) {
          chatId = update.callback_query.message.chat.id;
          userText = update.callback_query.data;
          callbackQueryId = update.callback_query.id;

          // Ignora se clicar nos cabeçalhos de texto
          if (userText === "ignore") {
            ctx.waitUntil(
              fetch(`https://api.telegram.org/bot${env.TELEGRAM_TOKEN}/answerCallbackQuery`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ callback_query_id: callbackQueryId })
              })
            );
            return new Response("OK");
          }
        } else if (update.message && update.message.text) {
          chatId = update.message.chat.id;
          userText = update.message.text;
        }

        if (!chatId || !userText) {
          return new Response("OK");
        }

        // --- 2. LÓGICA DO RANKING (Mantida original) ---
        if (userText === "📊 Ranking") {
          if (callbackQueryId) {
            ctx.waitUntil(fetch(`https://api.github.com/bot${env.TELEGRAM_TOKEN}/answerCallbackQuery`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ callback_query_id: callbackQueryId })
            }));
          }

          const rankingTask = fetch(`https://api.github.com/repos/${env.GITHUB_USER}/${env.GITHUB_REPO}/dispatches`, {
            method: 'POST',
            headers: {
              "Authorization": `Bearer ${env.GITHUB_TOKEN}`,
              "Accept": "application/vnd.github+json",
              "User-Agent": "Cloudflare-Worker-Ponte"
            },
            body: JSON.stringify({
              event_type: "solicitar_ranking",
              client_payload: { chat_id: chatId.toString() }
            })
          });
          ctx.waitUntil(rankingTask);

          return new Response(JSON.stringify({
            method: "sendMessage",
            chat_id: chatId,
            text: "📊 *Consultando estatísticas...*\nEstou preparando o ranking de assertividade para você.",
            parse_mode: "Markdown"
          }), { headers: { "Content-Type": "application/json" } });
        }

        // --- 3. LÓGICA DOS FILTROS ACUMULATIVOS ---
        if (typeof userText === "string" && (userText.startsWith("cb_"))) {
          
          const cacheKey = `podeapostar_state_${chatId}`;
          
          // Recupera o estado atual ou inicia com as configurações de fábrica
          let escolhas = { bingo: "5", horario: "DIA", bilhete: "ACERTOS" };
          if (env.PAINEL_KV) {
            const estadoRaw = await env.PAINEL_KV.get(cacheKey);
            if (estadoRaw) escolhas = JSON.parse(estadoRaw);
          }

          // Se clicou no botão definitivo de gerar o bilhete
          if (userText === "cb_acao_GERAR") {
            const stringComposta = `BINGO:${escolhas.bingo}|HORA:${escolhas.horario}|TIPO:${escolhas.bilhete}`;

            ctx.waitUntil(
              fetch(`https://api.telegram.org/bot${env.TELEGRAM_TOKEN}/answerCallbackQuery`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                  callback_query_id: callbackQueryId,
                  text: "🚀 Enviando filtros combinados para o servidor!"
                })
              })
            );

            const githubTask = fetch(`https://api.github.com/repos/${env.GITHUB_USER}/${env.GITHUB_REPO}/dispatches`, {
              method: 'POST',
              headers: {
                "Authorization": `Bearer ${env.GITHUB_TOKEN}`,
                "Accept": "application/vnd.github+json",
                "User-Agent": "Cloudflare-Worker-Ponte"
              },
              body: JSON.stringify({
                event_type: "comando_telegram",
                client_payload: {
                  chat_id: chatId.toString(),
                  tipo: stringComposta
                }
              })
            });

            ctx.waitUntil(githubTask);
            return new Response("OK");
          }

          // Salva a alteração silenciosamente na memória RAM do Worker
          if (userText.startsWith("cb_bingo_")) escolhas.bingo = userText.split("_").pop();
          if (userText.startsWith("cb_hora_")) escolhas.horario = userText.split("_").pop();
          if (userText.startsWith("cb_tipo_")) escolhas.bilhete = userText.split("_").pop();

          // Grava a nova seleção discretamente no KV (sem alterar o layout da tela)
          if (env.PAINEL_KV) {
            await env.PAINEL_KV.put(cacheKey, JSON.stringify(escolhas), { expirationTtl: 1800 });
          }

          // Apenas desliga o reloginho nativo do clique para o botão parar de rodar
          if (callbackQueryId) {
            ctx.waitUntil(
              fetch(`https://api.telegram.org/bot${env.TELEGRAM_TOKEN}/answerCallbackQuery`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ callback_query_id: callbackQueryId })
              })
            );
          }

          return new Response("OK");
        }

        // --- 4. COMPATIBILIDADE COM BOTÕES FIXOS ANTIGOS ---
        const botoesBingo = {
          "🔥 Bingo 3": "bingo_3",
          "🔥 Bingo 5": "bingo_5",
          "💎 Bingo Pro": "bingo_premium"
        };

        if (botoesBingo[userText]) {
          const githubTask = fetch(`https://api.github.com/repos/${env.GITHUB_USER}/${env.GITHUB_REPO}/dispatches`, {
            method: 'POST',
            headers: {
              "Authorization": `Bearer ${env.GITHUB_TOKEN}`,
              "Accept": "application/vnd.github+json",
              "User-Agent": "Cloudflare-Worker-Ponte"
            },
            body: JSON.stringify({
              event_type: "comando_telegram",
              client_payload: { chat_id: chatId.toString(), tipo: botoesBingo[userText] }
            })
          });
          ctx.waitUntil(githubTask);

          return new Response(JSON.stringify({
            method: "sendMessage",
            chat_id: chatId,
            text: `⌛ *Processando ${userText}...*\nO bilhete aparecerá abaixo in instantes!`,
            parse_mode: "Markdown"
          }), { headers: { "Content-Type": "application/json" } });
        }

      } catch (e) {
        return new Response("Erro: " + e.message);
      }
    }
    return new Response("OK");
  }
};
