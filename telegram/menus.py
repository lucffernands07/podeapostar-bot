import os
import requests

def enviar_menu_bingo(chat_id, texto):
    """
    Envia o menu FIXO no rodapé do Telegram.
    Ajuste: Adicionado disable_web_page_preview e log de erro para debug.
    """
    token = os.getenv('TELEGRAM_TOKEN')
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True, # <--- ESSENCIAL para mensagens com muitos links
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
            "resize_keyboard": True,
            "persistent": True,
            "one_time_keyboard": False
        }
    }

    try:
        response = requests.post(url, json=payload)
        res_json = response.json()
        
        # Se a mensagem NÃO chegou, o log do GitHub Actions agora vai te dizer o porquê
        if not res_json.get("ok"):
            print(f"❌ ERRO TELEGRAM: {res_json.get('description')}")
            
            # Se o erro for o Markdown do bingo357, tenta enviar sem formatação
            if "can't parse entities" in res_json.get("description", "").lower():
                payload["parse_mode"] = None
                requests.post(url, json=payload)
                
        return res_json
    except Exception as e:
        print(f"❌ Erro na requisição ao Telegram: {e}")
        return {"ok": False}
        
