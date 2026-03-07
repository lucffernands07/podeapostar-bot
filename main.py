import os
import requests
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO --- #
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
HEADERS = {"User-Agent": "Mozilla/5.0"}

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=15)
    except: print("   ❌ Erro Telegram.")

def buscar_gols_reais(liga_id, team_id):
    """Varre o placar dos últimos 10 dias para achar gols reais"""
    gols_feitos = 0
    jogos_contados = 0
    over25 = 0
    
    for i in range(1, 11): # Volta até 10 dias
        data_str = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{liga_id}/scoreboard?dates={data_str}"
        try:
            res = requests.get(url, headers=HEADERS, timeout=5).json()
            for ev in res.get('events', []):
                teams = ev['competitions'][0]['competitors']
                if any(str(t['id']) == str(team_id) for t in teams):
                    t_alvo = next(t for t in teams if str(t['id']) == str(team_id))
                    t_rival = next(t for t in teams if str(t['id']) != str(team_id))
                    
                    gf = int(t_alvo.get('score', 0))
                    gr = int(t_rival.get('score', 0))
                    gols_feitos += gf
                    jogos_contados += 1
                    if (gf + gr) >= 3: over25 += 1
            if jogos_contados >= 4: break # Já temos dados suficientes
        except: continue
    
    return gols_feitos, over25, jogos_contados

def executar_robo():
    hoje = datetime.now().strftime("%Y%m%d")
    print(f"🔎 SCANNER REAL-TIME: {hoje}")
    
    ligas = {"esp.1": "LALIGA", "eng.1": "Premier", "ger.1": "Bundes", "ita.1": "Serie A"}
    jogos_ok = []

    for l_id, l_nome in ligas.items():
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{l_id}/scoreboard?dates={hoje}"
            res = requests.get(url, headers=HEADERS, timeout=10).json()
            for ev in res.get('events', []):
                if ev.get('status', {}).get('type', {}).get('state') == 'pre':
                    c = ev['competitions'][0]['competitors']
                    h_id, a_id = c[0]['team']['id'], c[1]['team']['id']
                    h_nome, a_nome = c[0]['team']['displayName'], c[1]['team']['displayName']
                    
                    print(f"   ⏳ Analisando: {h_nome} x {a_nome}")
                    
                    # Pega os gols reais dos últimos jogos de cada um
                    gf_h, ov_h, cnt_h = buscar_gols_reais(l_id, h_id)
                    gf_a, ov_a, cnt_a = buscar_gols_reais(l_id, a_id)
                    
                    # LOGICA BARCELONA: Se o volume de gols marcados for alto
                    if gf_h >= 7 or gf_a >= 7 or (ov_h + ov_a) >= 4:
                        mercado = "🔥 +2.5 Gols" if (gf_h + gf_a) >= 10 else "⚽ +1.5 Gols"
                        jogos_ok.append(f"🏟️ *{h_nome} x {a_nome}*\n🎯 {mercado} `[Gols: {gf_h+gf_a} | 2.5: {ov_h+ov_a}]`")
        except: continue

    if jogos_ok:
        enviar_telegram("🏆 *🎯 BILHETE ATROPELO (DADOS REAIS)*\n\n" + "\n\n".join(jogos_ok))
    else:
        print("Nenhum atropelo identificado hoje.")

if __name__ == "__main__":
    executar_robo()
    
