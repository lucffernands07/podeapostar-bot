import os
import asyncio
import requests
from datetime import datetime

# --- CONFIGURAÇÃO --- #
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
API_KEY = os.getenv('X_RAPIDAPI_KEY') 
HEADERS = {'x-rapidapi-host': "api-football-v1.p.rapidapi.com", 'x-rapidapi-key': API_KEY}

def analisar_time(team_id, league_id, season):
    """ Busca estatísticas detalhadas do time na temporada atual """
    url = f"https://api-football-v1.p.rapidapi.com/v3/teams/statistics?league={league_id}&team={team_id}&season={season}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        data = res.get('response', {})
        if not data: return None
        
        # Extração de Dados Reais
        gols_jogos = data['goals']['for']['total']['total'] or 1
        gols_total = data['fixtures']['played']['total'] or 1
        
        return {
            "media_gols": gols_jogos / gols_total,
            "btts_perc": int(data.get('goals', {}).get('both_teams_score', {}).get('percentage', 0).replace('%','')),
            "clean_sheet": data['clean_sheet']['total'],
            "escanteios_avg": float(data.get('corners', {}).get('avg', 0) or 8.5)
        }
    except: return None

async def executar_robo():
    hoje = datetime.now().strftime("%Y-%m-%d")
    # LIGAS COMPLETAS (Adicionei mais para garantir os 10 jogos)
    ligas_config = {
        39: "Premier League", 140: "LALIGA", 141: "LaLiga 2", 78: "Bundesliga", 
        135: "Serie A", 61: "Ligue 1", 62: "Ligue 2", 94: "Português", 
        88: "Holandês", 40: "Championship", 71: "Brasileirão A", 
        471: "Paulistão", 472: "Carioca", 203: "Super Lig (Turquia)", 218: "Áustria"
    }
    
    jogos_analisados = []
    ligas_no_bilhete = set()

    for l_id, l_nome in ligas_config.items():
        season = 2026 if l_id in [71, 471, 472] else 2025
        url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={season}"
        
        res = requests.get(url, headers=HEADERS).json()
        for item in res.get('response', []):
            t1, t2 = item['teams']['home'], item['teams']['away']
            print(f"🔍 Validando: {t1['name']} x {t2['name']}...")
            
            s1 = analisar_time(t1['id'], l_id, season)
            s2 = analisar_time(t2['id'], l_id, season)

            if s1 and s2:
                # --- LÓGICA DE VALIDAÇÃO DE MERCADOS ---
                mercado = ""
                prio = 0
                
                media_combinada = (s1['media_gols'] + s2['media_gols']) / 2
                btts_medio = (s1['btts_perc'] + s2['btts_perc']) / 2
                cantos_medio = (s1['escanteios_avg'] + s2['escanteios_avg']) / 2

                if media_combinada > 2.8:
                    mercado = "⚡ +2.5 Gols — Atropelo"
                    prio = 100
                elif btts_medio > 65:
                    mercado = "🤝 Ambas Marcam — 4/5 (Est.)"
                    prio = 90
                elif media_combinada > 1.8:
                    mercado = "⚽ +1.5 Gols — Confiança Máxima"
                    prio = 80
                elif cantos_medio > 9.5:
                    mercado = "🚩 Mais de 8.5 Escanteios — Volume Alto"
                    prio = 70
                elif media_combinada > 1.2:
                    mercado = "🛡️ +0.5 Gols — Segurança"
                    prio = 60

                if mercado:
                    ligas_no_bilhete.add(l_nome)
                    jogos_analisados.append({
                        "prio": prio,
                        "liga": l_nome,
                        "texto": f"🏟️ *{t1['name']} x {t2['name']}*\n🕒 {item['fixture']['date'][11:16]} | {l_nome}\n🎯 {mercado}\n📊 [Estatísticas](https://www.sofascore.com/pt/futebol/jogo/{item['fixture']['id']})"
                    })

    if jogos_analisados:
        jogos_analisados.sort(key=lambda x: x['prio'], reverse=True)
        final = jogos_analisados[:10]
        final.sort(key=lambda x: x['liga'])
        
        msg = f"🎯 *BILHETE DO DIA ({len(final)} JOGOS)*\n💰🍀 BOA SORTE!!!\n\n"
        msg += "🏟️ *LIGAS ENCONTRADAS:*\n"
        for liga in sorted(list(ligas_no_bilhete)): msg += f"🔹 {liga}\n"
        msg += "\n"
        for i, jogo in enumerate(final, 1): msg += f"{i}. {jogo['texto']}\n\n"
        msg += "---\nAPOSTAR COM: 💸 [Bet365](https://www.bet365.com) | [Betano](https://www.betano.com)"
        enviar_telegram(msg)

if __name__ == "__main__":
    asyncio.run(executar_robo())
