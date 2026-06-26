import os
import requests

# Ajuste os caminhos de acordo com as pastas do seu repositório
PASTA_TELEGRAM = "telegram"

def extrair_markup_filtros(escolhas=None):
    """
    Menu dinâmico ajustado:
    - Lê o dicionário 'escolhas' vindo do Cloudflare/Bot.
    - Se não houver escolhas, assume o padrão estável.
    - Coloca marcadores visuais e injeta o estado no botão de disparo.
    """
    if not escolhas:
        escolhas = {"bingo": "5", "horario": "DIA", "bilhete": "ACERTOS"}

    # Extrai as strings salvando o estado atual
    b_atual = str(escolhas.get("bingo", "5"))
    h_atual = str(escolhas.get("horario", "DIA"))
    t_atual = str(escolhas.get("bilhete", "ACERTOS"))

    # 🟢 O SEGREDO: O botão de disparo agora leva as variáveis compactadas
    # permitindo que o Cloudflare as leia e envie ao processador.py
    callback_disparo = f"cb_acao_GERAR_B{b_atual}_{h_atual}_{t_atual}"

    return {
        "inline_keyboard": [
            # --- BOTÃO NO TOPO ---
            [
                {"text": "📊 RANKING DE MERCADOS ✅⛔", "callback_data": "cb_ver_ranking"}
            ],
            # --- SEÇÃO 1: BINGOS (Ganha marcação dinâmica) ---
            [{"text": f"✅ Escolha um bingo (Ativo: {b_atual} Jogos):", "callback_data": "ignore"}],
            [
                {
                    "text": "🟢 Bingo 3 (Denso)" if b_atual == "3" else "Bingo 3 (Denso)", 
                    "callback_data": "cb_bingo_3_ELITE"
                },
                {
                    "text": "🟢 Bingo 5 (Denso)" if b_atual == "5" else "Bingo 5 (Denso)", 
                    "callback_data": "cb_bingo_5_ELITE"
                }
            ],
            # --- SEÇÃO 2: HORÁRIOS ---
            [{"text": f"✅ Escolha uma janela (Ativa: {h_atual}):", "callback_data": "ignore"}],
            [
                {"text": "✨ Janela 3H" if h_atual == "3H" else "Janela 3H", "callback_data": "cb_hora_3H"},
                {"text": "✨ Janela 5H" if h_atual == "5H" else "Janela 5H", "callback_data": "cb_hora_5H"},
                {"text": "✨ Do Dia" if h_atual == "DIA" else "Do Dia", "callback_data": "cb_hora_DIA"}
            ],
            # --- SEÇÃO 3: ESTRATÉGIA ---
            [{"text": f"✅ Escolha um modo (Ativo: {t_atual}):", "callback_data": "ignore"}],
            [
                {"text": "🔥 Maiores Odds" if t_atual == "ODDS" else "Maiores Odds", "callback_data": "cb_tipo_ODDS"},
                {"text": "🔥 Mais acertos" if t_atual == "ACERTOS" else "Mais acertos", "callback_data": "cb_tipo_ACERTOS"},
                {"text": "🔥 Equilibrado" if t_atual == "AMBAS" else "Equilibrado", "callback_data": "cb_tipo_AMBAS"}
            ],
            # --- BOTÃO DE DISPARO DEFINITIVO COM ESTADO EMBUTIDO ---
            [
                {"text": "🚀 GERAR BILHETE", "callback_data": callback_disparo}
            ]
        ]
    }

def enviar_menu_bingo(chat_id, texto):
    """
    Disparado pelo main.py de madrugada.
    Envia a mensagem inicial acoplando o Painel com as escolhas padrão (5, DIA, ACERTOS).
    """
    token = os.getenv('TELEGRAM_TOKEN')
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    # Configuração inicial do painel padrão
    escolhas_padrao = {"bingo": "5", "horario": "DIA", "bilhete": "ACERTOS"}
    markup = extrair_markup_filtros(escolhas_padrao)

    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
        "reply_markup": markup
    }

    try:
        response = requests.post(url, json=payload)
        res_json = response.json()
        
        if not res_json.get("ok"):
            print(f"❌ ERRO TELEGRAM: {res_json.get('description')}")
            if "can't parse entities" in res_json.get("description", "").lower():
                payload["parse_mode"] = None
                response = requests.post(url, json=payload)
                res_json = response.json()
                
        return res_json
    except Exception as e:
        print(f"❌ Erro na requisição inicial do menu: {e}")
        return {"ok": False}


def atualizar_menu_inline(chat_id, message_id, texto, escolhas_atuais):
    """
    Função utilitária recuperada do commit histórico.
    Atualiza os botões inline em tempo real refletindo a escolha do usuário.
    """
    token = os.getenv('TELEGRAM_TOKEN')
    url = f"https://api.telegram.org/bot{token}/editMessageReplyMarkup"
    
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "reply_markup": extrair_markup_filtros(escolhas_atuais)
    }
    
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"❌ Erro ao atualizar os botões dinâmicos: {e}")
                
