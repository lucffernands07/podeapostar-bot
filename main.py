import os
import requests
from datetime import datetime, timedelta

# --- CONFIGURAÇÕES DE SEGURANÇA --- #
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
    """Busca os últimos 5 jogos de um time para análise de tendências."""
    hoje = datetime.now().strftime('%Y-%m-%d')
    ontem = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    # Buscamos um período longo para garantir que pegamos os últimos 5 finalizados
    params = {
        "team": team_name,
        "date_to": ontem,
        "status": "finished",
        "tz": "America/Sao_Paulo"
    }
    headers = {"Authorization": f"Token {BSD_TOKEN}"}
    try:
        res = requests.get(f"{BASE_URL}/events/", headers=headers, params=params)
        if res.status_code == 200:
            return res.json().get("results", [])[:5]
    except:
        return []
    return []

def analisar_partida(evento):
    home = evento['home_team']
    away = evento['away_team']
    
    hist_home = get_historico(home)
    hist_away = get_historico(away)
    
    if len(hist_home) < 5 or len(hist_away) < 5:
        return None

    # --- ANÁLISE DE GOLS ---
    def count_gols(jogos, threshold):
        count = 0
        for j in jogos:
            total = (j['home_score'] or 0) + (j['away_score'] or 0)
            if total > threshold: count += 1
        return count

    # Regra Gols: 5/5 e 5/5 (100%), 5/5 e 4/5 (85%), 4/5 e 4/5 (70%)
    gols_15_h = count_gols(hist_home, 1.5)
    gols_15_a = count_gols(hist_away, 1.5)
    
    chance_15 = 0
    if gols_15_h == 5 and gols_15_a == 5: chance_15 = 100
    elif (gols_15_h == 5 and gols_15_a == 4) or (gols_15_h == 4 and gols_15_a == 5): chance_15 = 85
    elif gols_15_h == 4 and gols_15_a == 4: chance_15 = 70

    # --- ANÁLISE 1X / 2X ---
    def get_stats(jogos, team_name):
        derrotas = 0
        for j in jogos:
            sou_home = j['home_team'] == team_name
            if sou_home and j['home_score'] < j['away_score']: derrotas += 1
            elif not sou_home and j['away_score'] < j['home_score']: derrotas += 1
        
        # Último resultado
        ult = jogos[0]
        vitoria_ult = False
        derrota_ult = False
        sou_home_ult = ult['home_team'] == team_name
        if sou_home_ult:
            if ult['home_score'] > ult['away_score']: vitoria_ult = True
            if ult['home_score'] < ult['away_score']: derrota_ult = True
        else:
            if ult['away_score'] > ult['home_score']: vitoria_ult = True
            if ult['away_score'] < ult['home_score']: derrota_ult = True
        return derrotas, vitoria_ult, derrota_ult

    d_h, vit_ult_h, derr_ult_h = get_stats(hist_home, home)
    d_a, vit_ult_a, derr_ult_a = get_stats(hist_away, away)

    mercado_vitoria = ""
    # 1X: Mandante max 1 derr + ult vitória | Visitante min 2 derr + ult derrota
    if d_h <= 1 and vit_ult_h and d_a >= 2 and derr_ult_a:
        mercado_vitoria = f"1X (Chance {80 if d_h == 0 else 60}%)"
    # 2X: Visitante 0 derrotas | Mandante min 2 derr + ult derrota
    elif d_a == 0 and d_h >= 2 and derr_ult_h:
        mercado_vitoria = f"2X (Chance 90%)"

    return {
        "home": home, "away": away,
        "hora": evento['event_date'].split("T")[1][:5],
        "chance_15": chance_15,
        "vitoria": mercado_vitoria,
        "chutes": 9.5 # Média fixa ou vinda de live_stats se disponível
    }

def realizar_analise():
    if not BSD_TOKEN: return
    hoje = datetime.now().strftime('%Y-%m-%d')
    headers = {"Authorization": f"Token {BSD_TOKEN}"}
    params = {"date_from": hoje, "date_to": hoje, "tz": "America/Sao_Paulo"}

    print(f"🚀 Analisando tendências para {hoje}...")
    res = requests.get(f"{BASE_URL}/events/", headers=headers, params=params)
    
    if res.status_code == 200:
        jogos = res.json().get("results", [])
        aprovados = []

        for j in jogos[:15]: # Limitando para não exceder tempo de execução
            analise = analisar_partida(j)
            if analise and (analise['chance_15'] > 0 or analise['vitoria']):
                aprovados.append(analise)
                print(f"✅ Analisado: {analise['home']} vs {analise['away']}")

        if aprovados:
            bilhete = "🎯 **BILHETE ESTRATÉGICO H2H**\n\n"
            for i, a in enumerate(aprovados, 1):
                bilhete += f"{i}. 🏟️ **{a['home']} x {a['away']}**\n"
                if a['chance_15'] > 0:
                    bilhete += f"🔶 Gols +1.5 (Chance {a['chance_15']}%)\n"
                if a['vitoria']:
                    bilhete += f"💎 Mercado: {a['vitoria']}\n"
                bilhete += f"🎯 Dica de escanteio -{a['chutes']}\n\n"
            
            enviar_telegram(bilhete)
            print("✉️ Bilhete enviado!")

if __name__ == "__main__":
    realizar_analise()
