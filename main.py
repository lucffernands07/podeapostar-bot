import requests

# Configurações de teste
HEADERS = {"User-Agent": "Mozilla/5.0"}
EVENT_ID = "706859"  # ID do jogo Athletic Club x Barcelona hoje
BARCA_ID = "83"      # ID do Barcelona na ESPN
ATHLETIC_ID = "93"   # ID do Athletic Club na ESPN

def testar_extracao():
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/summary?event={EVENT_ID}"
    print(f"🔎 Acessando API ESPN para o jogo ID: {EVENT_ID}...")
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        last_games = res.get('lastGames', [])
        
        if not last_games:
            print("❌ ERRO: A API não retornou a seção 'lastGames'.")
            return

        for t_group in last_games:
            t_id = str(t_group.get('teamId'))
            nome_time = "BARCELONA" if t_id == BARCA_ID else "ATHLETIC CLUB" if t_id == ATHLETIC_ID else f"TIME_{t_id}"
            
            print(f"\n--- {nome_time} (ID: {t_id}) ---")
            eventos = t_group.get('events', [])
            
            if not eventos:
                print(f"⚠️ Nenhum histórico encontrado para {nome_time}.")
                continue

            gols_total = 0
            jogos_over_15 = 0
            jogos_over_25 = 0

            for i, ev in enumerate(eventos[-5:], 1):
                try:
                    comp = ev.get('competitions', [{}])[0]
                    teams = comp.get('competitors', [])
                    
                    # Identifica quem é o time alvo no histórico
                    t_alvo = next(t for t in teams if str(t['id']) == t_id)
                    t_rival = next(t for t in teams if str(t['id']) != t_id)
                    
                    g_marcado = int(t_alvo.get('score', 0))
                    g_sofrido = int(t_rival.get('score', 0))
                    total_jogo = g_marcado + g_sofrido
                    
                    print(f"  Jogo {i}: {t_alvo['team']['displayName']} {g_marcado} x {g_sofrido} {t_rival['team']['displayName']}")
                    
                    gols_total += g_marcado
                    if total_jogo >= 2: jogos_over_15 += 1
                    if total_jogo >= 3: jogos_over_25 += 1
                except Exception as e:
                    print(f"  ⚠️ Erro no jogo {i}: {e}")

            print(f"📊 RESUMO {nome_time}:")
            print(f"   - Gols Marcados nos últimos 5: {gols_total}")
            print(f"   - Jogos +1.5 Gols: {jogos_over_15}/5")
            print(f"   - Jogos +2.5 Gols: {jogos_over_25}/5")

    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

if __name__ == "__main__":
    testar_extracao()
    
