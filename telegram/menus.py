import os
import json
import requests
from datetime import datetime

# Ajuste os caminhos de acordo com as pastas do seu repositório
PASTA_TELEGRAM = "telegram"

def extrair_markup_filtros(escolhas):
    """
    Desenha a matriz de botões inline com o layout exato solicitado.
    Usa prefixos nos callback_data para sabermos o que o usuário clicou.
    """
    b = escolhas.get("bingo", "5")
    h = escolhas.get("horario", "DIA")
    t = escolhas.get("bilhete", "ACERTOS")

    return {
        "inline_keyboard": [
            # --- SEÇÃO 1: BINGOS ---
            [{"text": "🎲 --- QUANTIDADE DE BINGOS ---", "callback_data": "ignore"}],
            [
                {"text": f"{'🟢' if b=='3' else '🔘'} [3]", "callback_data": "cb_bingo_3"},
                {"text": f"{'🟢' if b=='5' else '🔘'} [5]", "callback_data": "cb_bingo_5"},
                {"text": f"{'🟢' if b=='7' else '🔘'} [7]", "callback_data": "cb_bingo_7"}
            ],
            # --- SEÇÃO 2: HORÁRIOS ---
            [{"text": "⏱️ --- FILTRO DE HORÁRIO ---", "callback_data": "ignore"}],
            [
                {"text": f"{'🟢' if h=='3H' else '🔘'} [3H]", "callback_data": "cb_hora_3H"},
                {"text": f"{'🟢' if h=='5H' else '🔘'} [5H]", "callback_data": "cb_hora_5H"},
                {"text": f"{'🟢' if h=='DIA' else '🔘'} [DIA]", "callback_data": "cb_hora_DIA"}
            ],
            # --- SEÇÃO 3: TIPO DE BILHETE ---
            [{"text": "📊 --- ESTRATÉGIA DO BILHETE ---", "callback_data": "ignore"}],
            [
                {"text": f"{'🟢' if t=='ODDS' else '🔘'} [ODDS]", "callback_data": "cb_tipo_ODDS"},
                {"text": f"{'🟢' if t=='ACERTOS' else '🔘'} [ACERTOS]", "callback_data": "cb_tipo_ACERTOS"},
                {"text": f"{'🟢' if t=='AMBAS' else '🔘'} [AMBAS]", "callback_data": "cb_tipo_AMBAS"}
            ],
            # --- SEÇÃO 4: BOTÃO DE ENVIO (O GATILHO) ---
            [
                {"text": "🚀 GERAR E ENVIAR BILHETE", "callback_data": "cb_acao_gerar"}
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
    Função utilitária para o seu script que escuta cliques no Telegram.
    Sempre que clicarem num botão, chame essa função passando as novas escolhas
    para atualizar os emojis na tela na mesma hora usando 'editMessageReplyMarkup'.
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
        
