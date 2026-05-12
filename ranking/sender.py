import json
import os
import requests

PATH_DB = "ranking/ranking_db.json"

def get_barra_progresso(percentual):
    blocos = int(percentual / 20)
    return ("🟩" * blocos) + ("⬜" * (5 - blocos))

def gerar_tabela_ranking():
    if not os.path.exists(PATH_DB):
        return "📊 O ranking ainda está sendo processado..."

    with open(PATH_DB, 'r', encoding='utf-8') as f:
        db = json.load(f)
    
    stats = db.get("stats", {})
    if not stats:
        return "📭 Nenhuma estatística disponível."

    lista_ranking = []
    for mercado, dados in stats.items():
        g = dados.get('green', 0)
        r = dados.get('red', 0)
        total = g + r
        taxa = (g / total * 100) if total > 0 else 0
        
        # Limpando o nome do mercado para não quebrar o Markdown
        m_limpo = mercado.replace("_", " ").strip()
        
        lista_ranking.append({
            "mercado": m_limpo,
            "taxa": taxa,
            "green": g,
            "red": r
        })

    lista_ranking.sort(key=lambda x: (x['taxa'], x['green']), reverse=True)

    msg = "🏆 *RANKING DE ASSERTIVIDADE*\n"
    msg += f"📅 _Atualizado: {db.get('ultima_atualizacao', '---')}_\n\n"

    for i, item in enumerate(lista_ranking[:10], 1):
        medalha = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔹"
        barra = get_barra_progresso(item['taxa'])
        msg += f"{medalha} *{item['mercado']}*\n"
        msg += f"{barra} *{int(item['taxa'])}%* (✅ {item['green']} ❌ {item['red']})\n"
        msg += "--------------------------------\n"

    msg += "\n🔥 _Dados baseados no histórico real do bot._"
    return msg

def enviar_ranking_telegram(chat_id):
    token = os.getenv('TELEGRAM_TOKEN')
    texto = gerar_tabela_ranking()
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [
                [{"text": "🔥 Bingo 3", "callback_data": "🔥 Bingo 3"}, {"text": "🔥 Bingo 5", "callback_data": "🔥 Bingo 5"}],
                [{"text": "💎 Bingo Pro", "callback_data": "💎 Bingo Pro"}, {"text": "📊 Ranking", "callback_data": "📊 Ranking"}]
            ]
        }
    }
    
    response = requests.post(url, json=payload)
    res_json = response.json()
    
    # ISSO VAI APARECER NO LOG SE DER ERRO
    if not res_json.get("ok"):
        print(f"❌ ERRO TELEGRAM RANKING: {res_json.get('description')}")
        # Segunda tentativa sem Markdown caso tenha caracteres inválidos
        payload["parse_mode"] = None
        requests.post(url, json=payload)
    else:
        print(f"✅ Ranking enviado com sucesso para {chat_id}")
    
    return res_json
