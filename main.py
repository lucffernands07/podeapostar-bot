import os
import requests
from datetime import datetime, timedelta

# --- CONFIGURAÇÕES ---
BSD_TOKEN = os.getenv('BSD_TOKEN')
BASE_URL = "https://sports.bzzoiro.com/api"

def get_historico(team_id=None, team_name=None):
    """Busca histórico tentando ID primeiro, depois Nome, até achar 5 jogos."""
    ontem = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    headers = {"Authorization": f"Token {BSD_TOKEN}"}
    
    # Lista de tentativas para esgotar as chances de busca
    tentativas = []
    if team_id: 
        tentativas.append(("team_id", team_id))
    if team_name: 
        tentativas.append(("team", team_name))

    for chave, valor in tentativas:
        if not valor: continue
        params = {
            chave: valor, 
            "date_to": ontem, 
            "status": "finished", 
            "tz": "America/Sao_Paulo"
        }
        try:
            res = requests.get(f"{BASE_URL}/events/", headers=headers, params=params)
            if res.status_code == 200:
                resultados = res.json().get("results", [])
                
                # --- LINHA DE DEBUG (MATA A CHARADA DO ARSENAL) ---
                if len(resultados) > 0:
                    placares = [f"{j.get('home_score')}x{j.get('away_score')}" for j in resultados[:5]]
                    print(f"🏟️ Histórico encontrado para {valor} ({chave}): {placares}")

                # Mantém sua regra rígida: só aceita se encontrar os 5 jogos
                if len(resultados) >= 5:
                    return resultados[:5]
        except Exception as e:
            print(f"⚠️ Erro ao buscar histórico de {valor}: {e}")
            continue
            
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
    alvo = next((j for j in jogos if "Sporting" in j.get('home_team', '') or "Arsenal" in j.get('home_team', '')), None)

    if not alvo:
        print("❌ Jogo 'Sporting x Arsenal' não encontrado na grade de hoje da API.")
        return

    h_name = alvo.get('home_team')
    a_name = alvo.get('away_team')
    h_id = alvo.get('home_id') or alvo.get('home_team_id')
    a_id = alvo.get('away_id') or alvo.get('away_team_id')

    print(f"✅ Jogo localizado: {h_name} (ID: {h_id}) x {a_name} (ID: {a_id})")
    
    # --- 1. BUSCA DE HISTÓRICO ---
    hist_h = get_historico(team_id=h_id, team_name=h_name)
    hist_a = get_historico(team_id=a_id, team_name=a_name)

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

    # Sua regra exata de 4/5 ou 5/5
    if (g_h >= 4 and g_a >= 5) or (g_h >= 5 and g_a >= 4) or (g_h == 4 and g_a == 4):
        print("✅ PASSOU na regra de Gols +1.5!")
    else:
        print("❌ REPROVOU na regra de Gols +1.5 (Não atingiu 4/5 ou 5/5 combinados)")

    # --- 3. REGRA DE MERCADO (VITÓRIA) ---
    def debug_vitoria(jogos, t_name, t_id):
        derrotas = 0
        for j in jogos:
            # Se não temos ID, comparamos por nome (fallback inteligente)
            if t_id:
                h_id_hist = j.get('home_id') or j.get('home_team_id')
                sou_h = str(h_id_hist) == str(t_id)
            else:
                sou_h = j.get('home_team') == t_name
            
            h_s, a_s = j.get('home_score') or 0, j.get('away_score') or 0
            perdeu = (sou_h and h_s < a_s) or (not sou_h and a_s < h_s)
            if perdeu: derrotas += 1
        
        ult = jogos[0]
        h_s_u, a_s_u = ult.get('home_score') or 0, ult.get('away_score') or 0
        if t_id:
            h_id_u = ult.get('home_id') or ult.get('home_team_id')
            sou_h_u = str(h_id_u) == str(t_id)
        else:
            sou_h_u = ult.get('home_team') == t_name
            
        venceu_ult = (sou_h_u and h_s_u > a_s_u) or (not sou_h_u and a_s_u > h_s_u)
        return derrotas, venceu_ult

    d_h, v_h = debug_vitoria(hist_h, h_name, h_id)
    d_a, v_a = debug_vitoria(hist_a, a_name, a_id)

    print(f"💎 Stats Vitória -> Mandante: {d_h} derrotas, Vitória Ult: {v_h} | Visitante: {d_a} derrotas")

    if d_h <= 1 and v_h and d_a >= 2:
        print("✅ MERCADO: 1X Identificado")
    elif d_a == 0 and d_h >= 2:
        print("✅ MERCADO: 2X Identificado")
    else:
        print("ℹ️ MERCADO: Nenhuma Dupla Chance (1X/2X) atingiu o critério.")

if __name__ == "__main__":
    testar_jogo_especifico()
