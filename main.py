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
        print("✅ Mensagem enviada ao Telegram!")
    except:
        print("❌ Erro ao enviar Telegram")

def scan_adamchoi(team_id, team_name):
    """Busca os últimos 10 jogos e calcula a porcentagem real (Estilo AdamChoi)"""
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?team={team_id}&last=10"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        fixtures = res.get('response', [])
        if not fixtures: return 0, 0
        
        o15, o25 = 0, 0
        for f in fixtures:
            # Soma gols do jogo
            gols = (f['goals']['home'] or 0) + (f['goals']['away'] or 0)
            if gols >= 2: o15 += 1
            if gols >= 3: o25 += 1
            
        p_o15 = (o15 / len(fixtures)) * 100
        p_o25 = (o25 / len(fixtures)) * 100
        print(f"   📊 {team_name}: Over 1.5: {p_o15}% | Over 2.5: {p_o25}%")
        return p_o15, p_o25
    except:
        return 0, 0

def executar():
    hoje = datetime.now().strftime("%Y-%m-%d")
    print(f"🚀 INICIANDO VARREDURA ADAMCHOI: {hoje}")
    
    # Ligas principais (IDs atualizados)
    ligas = {
        135: "Serie A", 140: "LALIGA", 94: "Português", 239: "Colômbia", 
        203: "Süper Lig", 172: "Bulgária", 233: "Egito", 71: "Brasileirão A"
    }
    
    jogos_analisados = []

    for l_id, l_nome in ligas.items():
        # Define a temporada correta (Brasil/Colômbia = 2026, Europa = 2025)
        season = 2026 if l_id in [71, 239] else 2025
        url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={season}"
        
        try:
            res = requests.get(url, headers=HEADERS).json()
            matches = res.get('response', [])
            if not matches: continue
            
            print(f"\n✅ Verificando {l_nome} ({len(matches)} jogos encontrados)")
            
            for m in matches:
                t1_id, t1_name = m['teams']['home']['id'], m['teams']['home']['name']
                t2_id, t2_name = m['teams']['away']['id'], m['teams']['away']['name']
                
                print(f"🔍 Analisando: {t1_name} x {t2_name}")
                
                # CALCULA HISTÓRICO REAL (INDIVIDUAL)
                h_o15, h_o25 = scan_adamchoi(t1_id, t1_name)
                a_o15, a_o25 = scan_adamchoi(t2_id, t2_name)
                
                media_o15 = (h_o15 + a_o15) / 2
                media_o25 = (h_o25 + a_o25) / 2
                
                mercado = ""
                # REGRAS DO BILHETE (Baseadas no seu critério de 60% e 75%)
                if media_o25 >= 75:
                    mercado = "⚡ +2.5 Gols — Atropelo"
                elif media_o15 >= 75 or (60 <= media_o25 <= 74):
                    mercado = "⚽ +1.5 Gols — Confiança Máxima"
                elif 60 <= media_o15 <= 74:
                    mercado = "🛡️ +0.5 Gols — Segurança"

                if mercado:
                    jogos_analisados.append(
                        f"🏟️ *{t1_name} x {t2_name}*\n🕒 {m['fixture']['date'][11:16]} | {l_nome}\n🎯 {mercado}\n📊 [Estatísticas](https://www.sofascore.com/pt/futebol/jogo/{m['fixture']['id']})"
                    )
        except Exception as e:
            print(f"⚠️ Erro na liga {l_nome}: {e}")

    # ENVIAR PARA TELEGRAM
    if jogos_analisados:
        msg = "🎯 *BILHETE DO DIA (SISTEMA ADAMCHOI)*\n💰 BOA SORTE!\n\n"
        msg += "\n\n".join(jogos_analisados[:10])
        enviar_telegram(msg)
    else:
        print("⚠️ Nenhum jogo atingiu os critérios hoje.")

if __name__ == "__main__":
    executar()
    
