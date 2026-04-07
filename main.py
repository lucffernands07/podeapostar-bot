import os
import requests
from datetime import datetime, timedelta

# --- CONFIGURAÇÕES ---
BSD_TOKEN = os.getenv('BSD_TOKEN')
BASE_URL = "https://sports.bzzoiro.com/api"

def get_historico_debug(team_id, team_name):
    ontem = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    headers = {"Authorization": f"Token {BSD_TOKEN}"}
    
    # Tenta ID, depois Nome
    for chave, valor in [("team_id", team_id), ("team", team_name)]:
        if not valor: continue
        print(f"🔍 Tentando buscar histórico via {chave}: {valor}...")
        params = {chave: valor, "date_to": ontem, "status": "finished", "tz": "America/Sao_Paulo"}
        res = requests.get(f"{BASE_URL}/events/", headers=headers, params=params)
        
        if res.status_code == 200:
            jogos = res.json().get("results", [])
            print(f"📊 Encontrados {len(jogos)} jogos para {valor}.")
            if len(jogos) >= 5:
                return jogos[:5]
    return []

def testar_jogo_especifico():
    hoje = datetime.now().strftime('%Y-%m-%d')
    headers = {"Authorization": f"Token {BSD_TOKEN}"}
    params = {"date_from": hoje, "date_to": hoje, "tz": "America/Sao_Paulo"}

    print(f"🚀 Iniciando Teste Específico para Sporting x Arsenal ({hoje})")
    res = requests.get(f"{BASE_URL}/events/", headers=headers, params=params)
    
    if res.status_code != 200:
        print("❌ Erro ao conectar na API.")
        return

    jogos = res.json().get("results", [])
    # Filtra o jogo exato (usando 'in' para evitar erros de Sporting CP ou Arsenal FC)
    alvo = next((j for j in jogos if "Sporting" in j['home_team'] or "Arsenal" in j['home_team']), None)

    if not alvo:
        print("❌ Jogo 'Sporting x Arsenal' não encontrado na grade de hoje da API.")
        return

    print(f"✅ Jogo localizado: {alvo['home_team']} (ID: {alvo.get('home_id')}) x {alvo['away_team']} (ID: {alvo.get('away_id')})")
    
    # --- 1. BUSCA DE HISTÓRICO ---
    hist_h = get_historico_debug(alvo.get('home_id'), alvo['home_team'])
    hist_a = get_historico_debug(alvo.get('away_id'), alvo['away_team'])

    if len(hist_h) < 5 or len(hist_a) < 5:
        print(f"⛔ DESCARTADO: Histórico insuficiente (Home: {len(hist_h)}, Away: {len(hist_a)})")
        return

    # --- 2. REGRA DE GOLS +1.5 ---
    def check_gols(jogos, limite):
        sucessos = sum(1 for j in jogos if (j.get('home_score') or 0) + (j.get('away_score') or 0) > limite)
        return sucessos

    g_h = check_gols(hist_h, 1.5)
    g_a = check_gols(hist_a, 1.5)
    print(f"⚽ Gols +1.5 -> Mandante: {g_h}/5 | Visitante: {g_a}/5")

    if (g_h >= 4 and g_a >= 5) or (g_h >= 5 and g_a >= 4) or (g_h == 4 and g_a == 4):
        print("✅ PASSOU na regra de Gols +1.5!")
    else:
        print("❌ REPROVOU na regra de Gols +1.5 (Não atingiu 4/5 ou 5/5 combinados)")

    # --- 3. REGRA DE MERCADO (VITÓRIA) ---
    def debug_vitoria(jogos, t_name, t_id):
        derrotas = 0
        for j in jogos:
            # Comparação inteligente por ID para não errar o nome
            h_id_hist = j.get('home_id') or j.get('home_team_id')
            sou_h = str(h_id_hist) == str(t_id)
            
            h_s, a_s = j.get('home_score') or 0, j.get('away_score') or 0
            perdeu = (sou_h and h_s < a_s) or (not sou_h and a_s < h_s)
            if perdeu: derrotas += 1
        
        ult = jogos[0]
        h_id_u = ult.get('home_id') or ult.get('home_team_id')
        venceu_ult = (str(h_id_u) == str(t_id) and (ult['home_score'] > ult['away_score'])) or \
                     (str(h_id_u) != str(t_id) and (ult['away_score'] > ult['home_score']))
        return derrotas, venceu_ult

    d_h, v_h = debug_vitoria(hist_h, alvo['home_team'], alvo.get('home_id'))
    d_a, v_a = debug_vitoria(hist_a, alvo['away_team'], alvo.get('away_id'))

    print(f"💎 Stats Vitória -> Mandante: {d_h} derrotas, Vitória Ult: {v_h} | Visitante: {d_a} derrotas")

    if d_h <= 1 and v_h and d_a >= 2:
        print("✅ MERCADO: 1X Identificado")
    elif d_a == 0 and d_h >= 2:
        print("✅ MERCADO: 2X Identificado")
    else:
        print("ℹ️ MERCADO: Nenhuma Dupla Chance (1X/2X) atingiu o critério.")

if __name__ == "__main__":
    testar_jogo_especifico()
    
