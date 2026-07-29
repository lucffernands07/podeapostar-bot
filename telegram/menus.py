import os
import requests

# Ajuste os caminhos de acordo com as pastas do seu repositório
PASTA_TELEGRAM = "telegram"

def extrair_markup_filtros(escolhas=None):
    """
    Gera o teclado de botões para o Telegram.
    Layout com botões de Prováveis e Atualizar separados na linha abaixo do Ranking.
    """
    return {
        "inline_keyboard": [
            
            # --- SEÇÃO 1: BINGOS (Bingo 3 e 5) ---
            [{"text": "✅ Escolha um bingo:", "callback_data": "ignore"}],
            [
                {"text": "Bingo 3", "callback_data": "cb_bingo_3"},
                {"text": "Bingo 5", "callback_data": "cb_bingo_5"}
            ],
            # --- SEÇÃO 2: HORÁRIOS ---
            [{"text": "✅ Escolha uma janela:", "callback_data": "ignore"}],
            [
                {"text": "Janela 3H", "callback_data": "cb_hora_3H"},
                {"text": "Janela 5H", "callback_data": "cb_hora_5H"},
                {"text": "Próximos", "callback_data": "cb_hora_PROXIMOS"}
            ],
            # --- BOTÃO DE DISPARO DEFINITIVO ---
            [
                {"text": "🚀 GERAR BILHETE", "callback_data": "cb_acao_GERAR"}
            ],
            # --- LINHA RANKING SOLO ---
            [
                {"text": "📊 Ranking", "callback_data": "cb_ver_ranking"}
            ],
            # --- LINHA PROVÁVEIS E ATUALIZAR LADO A LADO ---
            [
                {"text": "👕 Prováveis", "callback_data": "cb_provaveis"},
                {"text": "🔄 Atualizar", "callback_data": "cb_atualizar_provaveis"}
            ]
        ]
    }

def enviar_menu_bingo(chat_id, texto):
    """
    Disparado pelo main.py de madrugada.
    Envia a mensagem inicial acoplando o Painel com as escolhas padrão (5 e PROXIMOS).
    """
    token = os.getenv('TELEGRAM_TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN')
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    # Configuração inicial do painel padrão
    escolhas_padrao = {"bingo": "5", "horario": "PROXIMOS"}
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
    Função utilitária para atualizar os botões na tela usando 'editMessageReplyMarkup'.
    """
    token = os.getenv('TELEGRAM_TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN')
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
    
