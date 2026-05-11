import os
import requests

def enviar_menu_bingo(chat_id, texto):
    """
    Envia a mensagem de sugestões com os botões de Bingo e Ranking.
    Layout: 
    🔥 Bingo 3   | 🔥 Bingo 5
    💎 Bingo Pro | 📊 Ranking
    """
    token = os.getenv('TELEGRAM_TOKEN')
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [
                [
                    {"text": "🔥 Bingo 3", "callback_data": "bingo_3"},
                    {"text": "🔥 Bingo 5", "callback_data": "bingo_5"}
                ],
                [
                    {"text": "💎 Bingo Pro", "callback_data": "bingo_premium"},
                    {"text": "📊 Ranking", "callback_data": "exibir_ranking"} 
                ]
            ]
        }
    }

    response = requests.post(url, json=payload)
    return response.json()
    
