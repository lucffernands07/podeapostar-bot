import os
import requests

def enviar_menu_bingo(chat_id, texto):
    """
    Envia o menu FIXO no rodapé do Telegram.
    Diferença: Agora os botões ficam no lugar do teclado.
    """
    token = os.getenv('TELEGRAM_TOKEN')
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "Markdown",
        "reply_markup": {
            "keyboard": [
                [
                    {"text": "🔥 Bingo 3"},
                    {"text": "🔥 Bingo 5"}
                ],
                [
                    {"text": "💎 Bingo Pro"},
                    {"text": "📊 Ranking"} 
                ]
            ],
            "resize_keyboard": True,   # Deixa os botões em tamanho pequeno/médio
            "persistent": True,        # Mantém o menu visível sempre
            "one_time_keyboard": False # Não esconde o menu após clicar
        }
    }

    response = requests.post(url, json=payload)
    return response.json()
    
