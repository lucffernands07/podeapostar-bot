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

def get_stats_e_historico(team_name):
    """Busca os últimos 5 jogos e calcula a média real de chutes ao gol."""
    ontem = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    headers = {"Authorization": f"Token {BSD_TOKEN}"}
    params = {
        "team": team_name,
        "date_to": ontem,
        "status": "finished",
        "tz": "America/Sao_Paulo"
    }
    
    chutes_totais = 0
    jogos_contados = 0
    historico = []

    try:
        res = requests.get(f"{BASE_URL}/events/", headers=headers, params=params)
        if res.status_code == 200:
            historico = res.json().get("results", [])[:5]
            for j in historico:
                # Busca os stats detalhados de cada partida do histórico
                res_detalhe = requests.get(f"{BASE_URL}/events/{j['id']}/", headers=headers)
                if res_detalhe.status_code == 200:
                    detalhes = res_detalhe.json()
                    is_home = detalhes['home_team'] == team_name
                    stats = detalhes.get("live_stats", {})
                    if stats:
                        lado = "home" if is_home else "away"
                        chutes = stats.get(lado, {}).get("shots_on_target", 0)
                        chutes_totais += chutes
                        jogos_contados += 1
    except Exception as e:
        print(f"⚠️ Erro ao buscar stats de {team_name}: {e}")

    media_chutes = (chutes_totais / jogos_contados) if jogos_contados > 0 else 4.0
    return historico, media_chutes

def analisar_partida(evento):
    home = evento['home_team']
    away = evento['away_team']
    
    hist_home, media_h = get_stats_e_historico(home)
    hist_away, media_a = get_stats_e_historico(away)
    
    if len(hist_home) < 4 or len(hist_away) < 4:
        return None

    # --- CÁLCULO ESCANTEIOS (Sempre sinaliza "menos") ---
    soma_chutes = media_h + media_a
    dica_escanteio = f"menos {soma_chutes:.1f}"

    # --- ANÁLISE DE GOLS ---
    def count_gols(jogos, threshold):
        return sum(1 for j in jogos if (j['home_score'] or 0) + (j['away_score'] or 0) > threshold)

    g15_h = count_gols(hist_home, 1.5)
    g15_a = count_gols(hist_away, 1.5)
    
    chance_15 = 0
    if g15_h == 5 and g15_a == 5: chance_15 = 100
    elif (g15_h == 5 and g15_a == 4) or (g15_h == 4 and g15_a == 5): chance_15 = 85
    elif g15_h == 4 and g15_a == 4: chance_15 = 70

    # --- ANÁLISE 1X / 2X ---
    def get_vitoria_stats(jogos, team_name):
        derrotas = 0
        for j in jogos:
            sou_home = j['home_team'] == team_name
            if (sou_home and j['home_score'] < j['away_score']) or (not sou_home and j['away_score'] < j['home_score']):
                derrotas += 1
        ult = jogos[0]
        sou_home_ult = ult['home_team'] == team_name
        vitoria_ult = (sou_home_ult and ult['home_score'] > ult['away_score']) or (not sou_home_ult and ult['away_score'] > ult['home_score'])
        derrota_ult = (sou_home_ult and ult['home_score'] < ult['away_score']) or (not sou_home_ult and ult['away_score'] < ult['home_score'])
        return derrotas, vitoria_ult, derrota_ult

    d_h, vit_u_h, _ = get_vitoria_stats(hist_home, home)
    d_a, _, derr_u_a = get_vitoria_stats(hist_away, away)

    mercado_vitoria = ""
    if d_h <= 1 and vit_u_h and d_a >= 2 and derr_u_a:
        mercado_vitoria = f"1X (Chance {80 if d_h == 0 else 65}%)"
    elif d_a == 0 and d_h >= 2:
        mercado_vitoria = f"2X (Chance 90%)"

    return {
        "home": home, "away": away,
        "chance_15": chance_15,
        "vitoria": mercado_vitoria,
        "escanteio": dica_escanteio
    }

def realizar_analise():
    if not BSD_TOKEN: return
    hoje = datetime.now().strftime('%Y-%m-%d')
    headers = {"Authorization": f"Token {BSD_TOKEN}"}
    params = {"date_from": hoje, "date_to": hoje, "tz": "America/Sao_Paulo"}

    print(f"🚀 Iniciando Mineração via API BSD para {hoje}...")
    res = requests.get(f"{BASE_URL}/events/", headers=headers, params=params)
    
    if res.status_code == 200:
        jogos = res.json().get("results", [])
        aprovados = []

        for j in jogos[:12]: # Analisa os 12 primeiros para evitar lentidão excessiva
            analise = analisar_partida(j)
            if analise:
                aprovados.append(analise)
                print(f"✅ Analisado: {analise['home']} vs {analise['away']} | Chutes: {analise['escanteio']}")

        if aprovados:
            bilhete = "🎯 **BILHETE ESTRATÉGICO H2H**\n\n"
            for i, a in enumerate(aprovados, 1):
                bilhete += f"{i}. 🏟️ **{a['home']} x {a['away']}**\n"
                if a['chance_15'] > 0:
                    bilhete += f"🔶 Gols +1.5 (Chance {a['chance_15']}%)\n"
                if a['vitoria']:
                    bilhete += f"💎 Mercado: {a['vitoria']}\n"
                bilhete += f"🚩 Dica de escanteio: {a['escanteio']}\n\n"
            
            enviar_telegram(bilhete)
            print("✉️ Bilhete enviado!")

if __name__ == "__main__":
    realizar_analise()
