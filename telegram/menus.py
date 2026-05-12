import os
import requests

def enviar_menu_bingo(chat_id, texto):
    """
    Envia o Bingo com os botões INLINE grudados na mensagem.
    """
    token = os.getenv('TELEGRAM_TOKEN')
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    # Criando os botões no formato INLINE (igual ao que funcionou no Ranking)
    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
        "reply_markup": {
            "inline_keyboard": [
                [
                    {"text": "🔥 Bingo 3", "callback_data": "🔥 Bingo 3"},
                    {"text": "🔥 Bingo 5", "callback_data": "🔥 Bingo 5"}
                ],
                [
                    {"text": "💎 Bingo Pro", "callback_data": "💎 Bingo Pro"},
                    {"text": "📊 Ranking", "callback_data": "📊 Ranking"}
                ]
            ]
        }
    }

    try:
        response = requests.post(url, json=payload)
        res_json = response.json()
        
        if not res_json.get("ok"):
            print(f"❌ ERRO TELEGRAM: {res_json.get('description')}")
            # Se der erro de Markdown (comum nos bingos pelos nomes dos times), envia sem formatacao
            if "can't parse entities" in res_json.get("description", "").lower():
                payload["parse_mode"] = None
                requests.post(url, json=payload)
                
        return res_json
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return {"ok": False}
