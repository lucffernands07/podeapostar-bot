import os
import requests

def enviar_menu_bingo(chat_id, texto):
    """
    Envia o menu FIXO no rodapé. 
    Corrigido para garantir que o Telegram aceite como ReplyKeyboardMarkup.
    """
    token = os.getenv('TELEGRAM_TOKEN')
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    # Criando a estrutura do teclado fixo (Reply Keyboard)
    teclado = {
        "keyboard": [
            [{"text": "🔥 Bingo 3"}, {"text": "🔥 Bingo 5"}],
            [{"text": "💎 Bingo Pro"}, {"text": "📊 Ranking"}]
        ],
        "resize_keyboard": True,
        "persistent": True,
        "one_time_keyboard": False
    }

    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
        "reply_markup": teclado  # Enviando como objeto puro
    }

    try:
        response = requests.post(url, json=payload)
        res_json = response.json()
        
        if not res_json.get("ok"):
            # Se ele ainda reclamar de "inline keyboard", vamos tentar remover o parse_mode
            # ou verificar se há algum conflito com mensagens anteriores.
            print(f"❌ ERRO TELEGRAM: {res_json.get('description')}")
            
            if "can't parse entities" in res_json.get("description", "").lower():
                payload["parse_mode"] = None
                response = requests.post(url, json=payload)
                res_json = response.json()
                
        return res_json
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return {"ok": False}
        
