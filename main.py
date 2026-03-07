import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}
BARCA_ID = "83"

def teste_resolucao_barcelona():
    print(f"🚀 TENTATIVA FINAL: EXTRAÇÃO VIA EVENTOS (BARCELONA)")
    # Esta URL traz o histórico de partidas com placar sem depender da aba 'stats'
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/teams/{BARCA_ID}/schedule"
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        eventos = res.get('events', [])
        
        gols_encontrados = []
        
        for ev in eventos:
            # Verifica se o jogo já aconteceu (tem placar e status 'post')
            if ev.get('status', {}).get('type', {}).get('state') == 'post':
                comp = ev.get('competitions', [{}])[0]
                teams = comp.get('competitors', [])
                
                t_barca = next(t for t in teams if str(t['id']) == BARCA_ID)
                t_rival = next(t for t in teams if str(t['id']) != BARCA_ID)
                
                gm = int(t_barca.get('score', 0))
                gr = int(t_rival.get('score', 0))
                data = ev.get('date', '')[:10]
                
                gols_encontrados.append({"data": data, "placar": f"Barça {gm} x {gr} {t_rival['team']['displayName']}", "gm": gm})

        # Pega os últimos 5
        ultimos = gols_encontrados[-5:]
        
        if ultimos:
            print("\n✅ SUCESSO! GOLS LOCALIZADOS:")
            total_gm = 0
            for j in ultimos:
                print(f"   📅 {j['data']} | {j['placar']}")
                total_gm += j['gm']
            
            print(f"\n📊 TOTAL DE GOLS MARCADOS (5 JOGOS): {total_gm}")
            print("💡 Se você está vendo os placares acima, o Barcelona está RESOLVIDO.")
        else:
            print("\n❌ A API de Schedule também não retornou placares.")

    except Exception as e:
        print(f"❌ Erro técnico: {e}")

if __name__ == "__main__":
    teste_resolucao_barcelona()
    
