import os
import requests

def enviar_menu_bingo(chat_id, texto):
    """
    Envia a mensagem de sugestões com botões inline para gerar novos bingos.
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
                    {"text": "🎰 Bingo 3", "callback_data": "bingo_3"},
                    {"text": "🎰 Bingo 5", "callback_data": "bingo_5"}
                ],
                [
                    {"text": "🎰 Bingo 7", "callback_data": "bingo_7"},
                    {"text": "🎰 Bingo 10", "callback_data": "bingo_10"}
                ]
            ]
        }
    }

    response = requests.post(url, json=payload)
    return response.json()
  
