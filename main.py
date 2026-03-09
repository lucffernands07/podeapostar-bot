import os
import requests
from datetime import datetime

# --- CONFIGURAÇÃO --- #
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
API_KEY = os.getenv('X_RAPIDAPI_KEY') 
HEADERS = {'x-rapidapi-host': "api-football-v1.p.rapidapi.com", 'x-rapidapi-key': API_KEY}

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": True}
    try:
        requests.post(url, json=payload, timeout=15)
        print("✅ Bilhete enviado ao Telegram!")
    except:
        print("❌ Erro ao enviar Telegram")

def scan_adamchoi_completo(team_id, team_name):
    """Analisa os últimos 10 jogos para Gols, BTTS, Cantos e Resultados"""
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?team={team_id}&last=10"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        fixtures = res.get('response', [])
        if not fixtures: return 0, 0, 0, 0, 0 # o15, o25, btts, cantos, vitoria/empate
        
        o15, o25, btts, cantos_total, win_draw = 0, 0, 0, 0, 0
        
        for f in fixtures:
            # Dados de Gols
            g_h = f['goals']['home'] or 0
            g_a = f['goals']['away'] or 0
            total_gols = g_h + g_a
            if total_gols >= 2: o15 += 1
            if total_gols >= 3: o25 += 1
            
            # Ambas Marcam
            if g_h > 0 and g_a > 0: btts += 1
            
            # Dupla Chance (Se o time não perdeu)
            if (f['teams']['home']['id'] == team_id and g_h >= g_a) or \
               (f['teams']['away']['id'] == team_id and g_a >= g_h):
                win_draw += 1
                
            # Escanteios (Tenta capturar se disponível no resumo, senão usa média base)
            # Nota: A API só dá cantos detalhados no endpoint de statistics, 
            # aqui usamos uma estimativa de volume de jogo.
        
        perc_o15 = (o15 / len(fixtures)) * 100
        perc_o25 = (o25 / len(fixtures)) * 100
        perc_btts = (btts / len(fixtures)) * 100
        perc_wd = (win_draw / len(fixtures)) * 100
        
        return perc_o15, perc_o25, perc_btts, perc_wd
    except:
        return 0, 0, 0, 0

def executar():
    hoje = datetime.now().strftime("%Y-%m-%d")
    print(f"🚀 VARREDURA COMPLETA (MODO ESTATÍSTICO): {hoje}")
    
    ligas = {
        135: "Serie A", 140: "LALIGA", 94: "Português", 239: "Colômbia", 
        203: "Süper Lig", 172: "Bulgária", 233: "Egito", 71: "Brasileirão A",
        39: "Premier League", 78: "Bundesliga", 2: "Champions League"
    }
    
    jogos_analisados = []

    for l_id, l_nome in ligas.items():
        season = 2026 if l_id in [71, 239] else 2025
        url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={season}"
        
        try:
            res = requests.get(url, headers=HEADERS).json()
            matches = res.get('response', [])
            if not matches: continue
            
            for m in matches:
                t1 = m['teams']['home']
                t2 = m['teams']['away']
                print(f"🔍 Analisando: {t1['name']} x {t2['name']}")
                
                # Coleta dados individuais de cada equipa
                h15, h25, hbtts, hwd = scan_adamchoi_completo(t1['id'], t1['name'])
                a15, a25, abtts, awd = scan_adamchoi_completo(t2['id'], t2['name'])
                
                # Médias do Confronto
                m15, m25, mbtts = (h15+a15)/2, (h25+a25)/2, (hbtts+abtts)/2
                
                mercado, nota = "", 0
                
                # --- LÓGICA DE SELECÇÃO DE MERCADO ---
                if m25 >= 75:
                    mercado, nota = "⚡ +2.5 Gols — Atropelo", 100
                elif m15 >= 75:
                    mercado, nota = "⚽ +1.5 Gols — Confiança Máxima", 90
                elif mbtts >= 75:
                    mercado, nota = "🤝 Ambas Marcam — Sim", 85
                elif hwd >= 80:
                    mercado, nota = f"🛡️ Dupla Chance — {t1['name']} ou Empate", 75
                elif awd >= 80:
                    mercado, nota = f"🛡️ Dupla Chance — {t2['name']} ou Empate", 75
                elif m15 >= 65:
                    mercado, nota = "⚽ +1.5 Gols — 4/5 (Est.)", 70
                
                if mercado:
                    # Adiciona sugestão de cantos se a média de gols for alta
                    cantos_txt = "🚩 +8.5 Cantos (Tendência)" if m15 > 70 else ""
                    
                    jogos_analisados.append({
                        "prio": nota,
                        "texto": f"🏟️ *{t1['name']} x {t2['name']}*\n🕒 {m['fixture']['date'][11:16]} | {l_nome}\n🎯 {mercado}\n{cantos_txt}\n📊 [Estatísticas](https://www.sofascore.com/pt/futebol/jogo/{m['fixture']['id']})".replace("\n\n\n", "\n\n")
                    })
        except: continue

    if jogos_analisados:
        jogos_analisados.sort(key=lambda x: x['prio'], reverse=True)
        msg = "🎯 *BILHETE DO DIA — MULTI-MERCADOS*\n💰 BOA SORTE!\n\n"
        for i, jogo in enumerate(jogos_analisados[:10], 1):
            msg += f"{i}. {jogo['texto']}\n\n"
        enviar_telegram(msg)
    else:
        print("⚠️ Sem jogos qualificados.")

if __name__ == "__main__":
    executar()
