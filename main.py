import os
import requests
from datetime import datetime, timedelta

# --- CONFIGURAÇÕES ---
BSD_TOKEN = os.getenv('BSD_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
BASE_URL = "https://sports.bzzoiro.com/api"

def enviar_telegram(mensagem):
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

def get_historico(team_name):
    ontem = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    headers = {"Authorization": f"Token {BSD_TOKEN}"}
    params = {"team": team_name, "date_to": ontem, "status": "finished", "tz": "America/Sao_Paulo"}
    try:
        res = requests.get(f"{BASE_URL}/events/", headers=headers, params=params)
        if res.status_code == 200:
            return res.json().get("results", [])[:5]
    except: return []
    return []

def calcular_chance_gols(hist_h, hist_a, limite):
    def count_gols(jogos):
        return sum(1 for j in jogos if (j.get('home_score') or 0) + (j.get('away_score') or 0) > limite)
    
    g_h, g_a = count_gols(hist_h), count_gols(hist_a)
    if g_h == 5 and g_a == 5: return 100
    elif (g_h == 5 and g_a == 4) or (g_h == 4 and g_a == 5): return 85
    elif g_h == 4 and g_a == 4: return 70
    return 0

def analisar_partida(evento):
    home, away = evento['home_team'], evento['away_team']
    hist_h = get_historico(home)
    hist_a = get_historico(away)
    
    if len(hist_h) < 5 or len(hist_a) < 5: return None

    chance_15 = calcular_chance_gols(hist_h, hist_a, 1.5)
    chance_25 = calcular_chance_gols(hist_h, hist_a, 2.5)

    def get_vitoria_stats(jogos, team_name):
        derrotas = 0
        for j in jogos:
            sou_h = j.get('home_team') == team_name
            h_s, a_s = j.get('home_score') or 0, j.get('away_score') or 0
            if (sou_h and h_s < a_s) or (not sou_h and a_s < h_s): derrotas += 1
        
        if not jogos: return 5, False
        ult = jogos[0]
        sou_h_u = ult.get('home_team') == team_name
        h_u, a_u = ult.get('home_score') or 0, ult.get('away_score') or 0
        vit_u = (sou_h_u and h_u > a_u) or (not sou_h_u and a_u > h_u)
        return derrotas, vit_u

    d_h, v_h = get_vitoria_stats(hist_h, home)
    d_a, _ = get_vitoria_stats(hist_a, away)
    
    mercado = ""
    if d_h <= 1 and v_h and d_a >= 2: mercado = f"1X (Chance {80 if d_h == 0 else 65}%)"
    elif d_a == 0 and d_h >= 2: mercado = f"2X (Chance 90%)"

    return {
        "home": home, "away": away,
        "chance_15": chance_15,
        "chance_25": chance_25,
        "vitoria": mercado
    }

def realizar_analise():
    hoje = datetime.now().strftime('%Y-%m-%d')
    headers = {"Authorization": f"Token {BSD_TOKEN}"}
    
    # Removi o status do parâmetro para evitar que a API retorne vazio por erro de termo
    params = {
        "date_from": hoje, 
        "date_to": hoje, 
        "tz": "America/Sao_Paulo"
    }

    print(f"🚀 Buscando jogos para: {hoje}")
    res = requests.get(f"{BASE_URL}/events/", headers=headers, params=params)
    
    if res.status_code == 200:
        todos_jogos = res.json().get("results", [])
        print(f"📡 API retornou {len(todos_jogos)} jogos no total.") # Log para conferir
        
        bilhete = "🎯 **BILHETE ESTRATÉGICO H2H**\n\n"
        count = 0
        
        # Analisamos até 100 jogos da lista
        for j in todos_jogos[:100]:
            # Filtro manual de status: ignora só o que já acabou
            if j.get('status') == 'finished':
                continue
                
            a = analisar_partida(j)
            if a and (a['chance_15'] > 0 or a['chance_25'] > 0 or a['vitoria']):
                bilhete += f"{count+1}. 🏟️ **{a['home']} x {a['away']}**\n"
                if a['chance_15'] > 0: bilhete += f"🔶 Gols +1.5 (Chance {a['chance_15']}%)\n"
                if a['chance_25'] > 0: bilhete += f"🔷 Gols +2.5 (Chance {a['chance_25']}%)\n"
                if a['vitoria']: bilhete += f"💎 Mercado: {a['vitoria']}\n"
                bilhete += "---\n\n"
                count += 1
        
        if count > 0: 
            enviar_telegram(bilhete)
            print(f"✅ Bilhete enviado com {count} jogos!")
        else:
            print("ℹ️ Nenhum jogo passou nos critérios de 4/5 ou 5/5 hoje.")

if __name__ == "__main__":
    realizar_analise()
