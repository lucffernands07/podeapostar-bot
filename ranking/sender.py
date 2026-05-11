import json
import os
import requests

PATH_DB = "ranking/ranking_db.json"

def gerar_tabela_ranking():
    if not os.path.exists(PATH_DB):
        return "📊 O ranking ainda está sendo processado. Tente novamente mais tarde!"

    with open(PATH_DB, 'r', encoding='utf-8') as f:
        db = json.load(f)
    
    stats = db.get("stats", {})
    if not stats:
        return "📭 Nenhuma estatística disponível no momento."

    # 1. Preparar os dados para ordenação
    lista_ranking = []
    for mercado, dados in stats.items():
        g = dados.get('green', 0)
        r = dados.get('red', 0)
        total = g + r
        taxa = (g / total * 100) if total > 0 else 0
        lista_ranking.append({
            "mercado": mercado,
            "taxa": taxa,
            "green": g,
            "red": r,
            "total": total
        })

    # 2. Ordenar por % de acerto e depois por quantidade de Green
    lista_ranking.sort(key=lambda x: (x['taxa'], x['green']), reverse=True)

    # 3. Montar a mensagem em Markdown (Tabela Simplificada)
    msg = "🏆 *RANKING DE ASSERTIVIDADE*\n"
    msg += f"📅 Atualizado em: {db.get('ultima_atualizacao', '---')}\n\n"
    msg += "`MERCADO         | %    | G | R `\n"
    msg += "--------------------------------\n"

    for i, item in enumerate(lista_ranking[:15], 1): # Top 15 para não cortar o texto
        # Ajusta o nome do mercado para caber na tabela (max 15 caracteres)
        nome = (item['mercado'][:13] + "..") if len(item['mercado']) > 15 else item['mercado'].ljust(15)
        taxa_str = f"{int(item['taxa'])}%".ljust(4)
        msg += f"`{nome} | {taxa_str} | {item['green']} | {item['red']}`\n"

    msg += "\n🔥 _Dados baseados nos últimos jogos processados._"
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
  
