import os
import requests

def enviar_menu_bingo(chat_id, texto):
    """
    Volta para botões INLINE (dentro da mensagem) para resolver o erro 
    de 'inline keyboard expected'.
    """
    token = os.getenv('TELEGRAM_TOKEN')
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    # Estrutura INLINE (a que o seu bot espera)
    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
        "reply_markup": {
            "inline_keyboard": [
                [
                    {"text": "🔥 Bingo 3", "callback_data": "bingo_3"},
                    {"text": "🔥 Bingo 5", "callback_data": "bingo_5"}
                ],
                [
                    {"text": "💎 Bingo Pro", "callback_data": "bingo_pro"},
                    {"text": "📊 Ranking", "callback_data": "ranking"}
                ]
            ]
        }
    }

    try:
        response = requests.post(url, json=payload)
        res_json = response.json()
        
        if not res_json.get("ok"):
            print(f"❌ ERRO TELEGRAM: {res_json.get('description')}")
            # Se o problema for o Markdown do bingo357, tenta sem formatação
            if "can't parse entities" in res_json.get("description", "").lower():
                payload["parse_mode"] = None
                response = requests.post(url, json=payload)
                res_json = response.json()
                
        return res_json
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return {"ok": False}
        
