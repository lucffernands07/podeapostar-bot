import json
import os
import requests

PATH_DB = "ranking/ranking_db.json"

def get_barra_progresso(percentual):
    """Padroniza o emoji para evitar variações de tom no Telegram"""
    blocos = int(percentual / 20)
    # Copie exatamente estes caracteres:
    quadrado_cheio = "🟩" # U+1F7E9
    quadrado_vazio = "⬜️" # U+2B1C
    return (quadrado_cheio * blocos) + (quadrado_vazio * (5 - blocos))

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
        lista_ranking.append({
            "mercado": mercado.strip(), # Mantém o nome original com a (%)
            "taxa": taxa,
            "green": g,
            "red": r
        })

    # Ordenação: Taxa -> Greens
    lista_ranking.sort(key=lambda x: (x['taxa'], x['green']), reverse=True)

    msg = "🏆 *RANKING DE ASSERTIVIDADE*\n"
    msg += f"📅 _Atualizado: {db.get('ultima_atualizacao', '---')}_\n\n"

    for i, item in enumerate(lista_ranking[:10], 1):
        medalha = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔹"
        barra = get_barra_progresso(item['taxa'])
        
        # Mercado e (%) na mesma linha em negrito
        msg += f"{medalha} *{item['mercado']}*\n"
        # Barra e stats na linha de baixo
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
        "parse_mode": "Markdown"
    }
    
    return requests.post(url, json=payload).json()
        
