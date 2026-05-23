import os
import json
import requests
from datetime import datetime

# Ajuste os caminhos de acordo com as pastas do seu repositório
PASTA_TELEGRAM = "telegram"

def extrair_markup_filtros(escolhas=None):
    """
    Retorna o menu estático com os novos cabeçalhos solicitados pelo Luciano
    e o botão definitivo para disparo unificado.
    """
    return {
        "inline_keyboard": [
            # --- SEÇÃO 1: BINGOS ---
            [{"text": "✅ Escolha um bingo:", "callback_data": "ignore"}],
            [
                {"text": "Bingo 3", "callback_data": "cb_bingo_3"},
                {"text": "Bingo 5", "callback_data": "cb_bingo_5"},
                {"text": "Bingo 7", "callback_data": "cb_bingo_7"}
            ],
            # --- SEÇÃO 2: HORÁRIOS ---
            [{"text": "✅ Escolha uma janela:", "callback_data": "ignore"}],
            [
                {"text": "Janela 3H", "callback_data": "cb_hora_3H"},
                {"text": "Janela 5H", "callback_data": "cb_hora_5H"},
                {"text": "Do Dia", "callback_data": "cb_hora_DIA"}
            ],
            # --- SEÇÃO 3: ESTRATÉGIA ---
            [{"text": "✅ Escolha um modo:", "callback_data": "ignore"}],
            [
                {"text": "Maiores Odds", "callback_data": "cb_tipo_ODDS"},
                {"text": "Mais acertos", "callback_data": "cb_tipo_ACERTOS"},
                {"text": "Equilibrado", "callback_data": "cb_tipo_AMBAS"}
            ],
            # --- BOTÃO DE DISPARO DEFINITIVO ---
            [
                {"text": "🚀 GERAR BILHETE", "callback_data": "cb_acao_GERAR"}
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
    para atualizar os botões na tela usando 'editMessageReplyMarkup'.
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
