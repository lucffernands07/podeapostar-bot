def analisar_historico_adamchoi(team_id):
    """Simula a visão do AdamChoi: olha os últimos 10 jogos do time"""
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?team={team_id}&last=10"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        fixtures = res.get('response', [])
        if not fixtures: return 0
        
        jogos_com_over15 = 0
        for f in fixtures:
            gols_total = (f['goals']['home'] or 0) + (f['goals']['away'] or 0)
            if gols_total >= 2: # Over 1.5
                jogos_com_over15 += 1
        
        # Retorna a porcentagem (ex: 8 jogos de 10 = 80%)
        return (jogos_com_over15 / len(fixtures)) * 100
    except:
        return 0

def pegar_previsao(fixture_id, home_id, away_id):
    # Primeiro, pega a predição normal
    url = f"https://api-football-v1.p.rapidapi.com/v3/predictions?fixture={fixture_id}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=12).json()
        data = res['response'][0]
        p = data.get('predictions', {}).get('percent', {})
        
        # --- AGORA A MÁGICA DO ADAMCHOI ---
        # Se a API está "vazia" (como hoje), calculamos o histórico real
        perc_home = analisar_historico_adamchoi(home_id)
        perc_away = analisar_historico_adamchoi(away_id)
        media_over15_real = (perc_home + perc_away) / 2

        print(f"   📊 AdamChoi Style -> Média Over 1.5 nos últimos 10 jogos: {media_over15_real}%", flush=True)

        # Se a média dos dois times for acima de 80% (como nas suas fotos), a gente força o palpite
        o15_final = int(str(p.get('over_1_5', '0')).replace('%',''))
        if o15_final < 60 and media_over15_real >= 80:
            o15_final = 85 # Força entrada por histórico real
            
        return {"o15": o15_final, "o25": 0, "home": 0, "away": 0} # Simplificado para teste
    except:
        return None
        
