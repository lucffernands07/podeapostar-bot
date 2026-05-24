import json
import os
import requests

# Importa o módulo de menus para pegar o painel padronizado
from telegram import menus

# --- AGORA APONTAMOS PARA O ARQUIVO PRÉ-MONTADO ---
PATH_RANKING_DIARIO = "ranking/ranking_diario.json"
PATH_DB = "ranking/ranking_db.json" # Mantido apenas para pegar a data de atualização

def get_barra_progresso(percentual):
    blocos = int(percentual / 20)
    return ("🟩" * blocos) + ("⬜" * (5 - blocos))

def gerar_tabela_ranking():
    # 1. Verifica se o ranking diário existe
    if not os.path.exists(PATH_RANKING_DIARIO):
        return "📊 O ranking diário ainda está sendo gerado pela madrugada..."

    # 2. Carrega o ranking já ordenado
    with open(PATH_RANKING_DIARIO, 'r', encoding='utf-8') as f:
        lista_ranking = json.load(f)
    
    if not lista_ranking:
        return "📭 Nenhuma estatística disponível no momento."

    # 3. Busca a data de atualização no banco principal (apenas para o cabeçalho)
    data_att = "---"
    if os.path.exists(PATH_DB):
        with open(PATH_DB, 'r', encoding='utf-8') as f:
            db_main = json.load(f)
            data_att = db_main.get('ultima_atualizacao', '---')

    # 4. Monta a Mensagem (A lógica de exibição permanece a mesma)
    msg = "🏆 *RANKING DE ASSERTIVIDADE*\n"
    msg += f"📅 _Atualizado: {data_att}_\n\n"

    # Pegamos os top 10 do arquivo que o ranking.py já ordenou
    for i, item in enumerate(lista_ranking[:10], 1):
        medalha = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔹"
        
        # O ranking_diario já tem a taxa (assertividade) calculada como decimal (ex: 1.0)
        taxa_cem = item['assertividade'] * 100
        barra = get_barra_progresso(taxa_cem)
        
        # Limpa o nome do mercado
        m_limpo = item['mercado'].replace("_", " ").strip()
        
        msg += f"{medalha} *{m_limpo}*\n"
        msg += f"{barra} *{int(taxa_cem)}%* (✅ {item['green']} ❌ {item['red']})\n"
        msg += "--------------------------------\n"

    msg += "\n🔥 _Dados baseados no histórico real do bot._"
    return msg

def enviar_ranking_telegram(chat_id):
    token = os.getenv('TELEGRAM_TOKEN')
    texto = gerar_tabela_ranking()
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # Gera o painel de botões no padrão do Luciano (5, DIA, ACERTOS) para acompanhar o ranking
    escolhas_padrao = {"bingo": "5", "horario": "DIA", "bilhete": "ACERTOS"}
    markup_atualizado = menus.extrair_markup_filtros(escolhas_padrao)
    
    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
        "reply_markup": markup_atualizado  # <--- AJUSTADO AQUI!
    }
    
    response = requests.post(url, json=payload)
    res_json = response.json()
    
    if not res_json.get("ok"):
        print(f"❌ ERRO TELEGRAM RANKING: {res_json.get('description')}")
        payload["parse_mode"] = None
        requests.post(url, json=payload)
    else:
        print(f"✅ Ranking enviado com sucesso para {chat_id}")
    
    return res_json
    
