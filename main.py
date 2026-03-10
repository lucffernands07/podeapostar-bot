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
        print("✅ Bilhete enviado ao Telegram!", flush=True)
    except:
        print("❌ Erro ao enviar Telegram", flush=True)

def get_adamchoi_stats(team_id):
    """Analisa os últimos 10 jogos para gerar as combinações (Estilo AdamChoi)"""
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?team={team_id}&last=10"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        fixtures = res.get('response', [])
        if not fixtures: return 0, 0, 0, 0
        
        o15, o25, btts, wd = 0, 0, 0, 0
        for f in fixtures:
            g_h = f['goals']['home'] if f['goals']['home'] is not None else 0
            g_a = f['goals']['away'] if f['goals']['away'] is not None else 0
            
            if (g_h + g_a) >= 2: o15 += 1
            if (g_h + g_a) >= 3: o25 += 1
            if g_h > 0 and g_a > 0: btts += 1
            
            # Vitória ou Empate (Dupla Chance)
            if (f['teams']['home']['id'] == team_id and g_h >= g_a) or \
               (f['teams']['away']['id'] == team_id and g_a >= g_h):
                wd += 1
        
        return (o15*10), (o25*10), (btts*10), (wd*10)
    except:
        return 0, 0, 0, 0

def executar():
    hoje = datetime.now().strftime("%Y-%m-%d")
    print(f"🚀 Gerando Bilhetes Combinados: {hoje}", flush=True)
    
    # MAPEAMENTO DE LINKS (SLUGS) PARA O ADAMCHOI
    ligas_config = {
        2: ("Champions", "uefa-champions-league"),
        39: ("Premier League", "premier-league"),
        140: ("LALIGA", "la-liga"),
        135: ("Serie A", "serie-a"),
        78: ("Bundesliga", "bundesliga"),
        94: ("Português", "primeira-liga"),
        71: ("Brasileirão A", "brazilian-serie-a"),
        239: ("Colômbia", "colombian-primera-a"),
        88: ("Holandês", "eredivisie"),
        203: ("Turquia", "turkish-super-lig"),
        61: ("Ligue 1", "ligue-1"),
        # Estaduais e Regionais
        73: ("Copa do Nordeste", "brazilian-copa-do-nordeste"),
        475: ("Carioca", "brazilian-carioca-a"),
        477: ("Paulista", "brazilian-paulista-a"),
        479: ("Gaúcho", "brazilian-gaucho-1"),
        480: ("Mineiro", "brazilian-mineiro-1")
    }
    
    bilhete_final = []
    ligas_encontradas = set()

    for l_id, (l_nome, l_slug) in ligas_config.items():
        # Temporada 2026 para Américas, 2025 para Europa
        season = 2026 if l_id in [71, 73, 239, 475, 477, 479, 480] else 2025
        url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={season}"
        
        try:
            res = requests.get(url, headers=HEADERS).json()
            matches = res.get('response', [])
            
            for m in matches:
                t1, t2 = m['teams']['home'], m['teams']['away']
                print(f"🔍 Analisando: {t1['name']} x {t2['name']}", flush=True)
                
                h15, h25, hbtts, hwd = get_adamchoi_stats(t1['id'])
                a15, a25, abtts, awd = get_adamchoi_stats(t2['id'])
                
                m15, m25, mbtts = (h15+a15)/2, (h25+a25)/2, (hbtts+abtts)/2
                
                opcoes = []
                prio = 0
                
                # REGRAS DE MERCADO
                # 1. Dupla Chance
                if hwd >= 80: 
                    opcoes.append(f"🔸 1X ({t1['name']} ou Empate)")
                    prio += 40
                elif awd >= 80: 
                    opcoes.append(f"🔸 X2 ({t2['name']} ou Empate)")
                    prio += 40
                
                # 2. Gols
                if m25 >= 70: 
                    opcoes.append("🔸 Mais de 2.5 Gols")
                    prio += 50
                elif m15 >= 75: 
                    opcoes.append("🔸 Mais de 1.5 Gols")
                    prio += 30
                
                # 3. Ambas Marcam
                if mbtts >= 75: 
                    opcoes.append("🔸 Ambas Marcam - Sim")
                    prio += 35
                
                # 4. Escanteios (Tendência por fluxo de gols)
                if m15 >= 80:
                    opcoes.append("🔸 +8.5 Escanteios (Tendência)")
                    prio += 10

                if opcoes:
                    ligas_encontradas.add(l_nome)
                    link_adam = f"https://www.adamchoi.co.uk/{l_slug}"
                    
                    titulo = "🔥 *Criar Aposta*" if len(opcoes) >= 2 else "🎯 *Aposta Simples*"
                    
                    bilhete_final.append({
                        "prio": prio,
                        "texto": f"🏟️ *{t1['name']} x {t2['name']}*\n🕒 {m['fixture']['date'][11:16]} | {l_nome}\n{titulo}\n" + "\n".join(opcoes) + f"\n📊 [Estatísticas]({link_adam})"
                    })
        except:
            continue

    if bilhete_final:
        # Ordena pelos jogos com mais "valor" (combinações)
        bilhete_final.sort(key=lambda x: x['prio'], reverse=True)
        
        msg = "🎯 *BILHETE DO DIA (10 JOGOS)*\n💰🍀 BOA SORTE!!!\n\n"
        msg += "🏟️ *LIGAS ENCONTRADAS:*\n"
        msg += "\n".join([f"🔹 {l}" for l in sorted(list(ligas_encontradas))])
        msg += "\n\n"
        
        for i, jogo in enumerate(bilhete_final[:10], 1):
            msg += f"{i}. {jogo['texto']}\n\n"
        
        msg += "---\nAPOSTAR COM: 💸 [Bet365](https://www.bet365.com) | [Betano](https://www.betano.com)"
        enviar_telegram(msg)
    else:
        print("⚠️ Nenhum jogo qualificado hoje.", flush=True)

if __name__ == "__main__":
    executar()
            
