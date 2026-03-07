import requests
import json

HEADERS = {"User-Agent": "Mozilla/5.0"}
BARCA_ID = "83"

def auditoria_bruta_barca():
    print(f"🔎 BUSCA TOTAL: BARCELONA (ID: {BARCA_ID})")
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/teams/{BARCA_ID}/schedule"
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        eventos = res.get('events', [])
        
        if not eventos:
            print("❌ Nenhum evento encontrado no JSON.")
            return

        jogos_com_placar = []
        for ev in eventos:
            try:
                # Pega o placar sem olhar o status (state)
                comp = ev.get('competitions', [{}])[0]
                teams = comp.get('competitors', [])
                t_barca = next(t for t in teams if str(t['id']) == BARCA_ID)
                t_rival = next(t for t in teams if str(t['id']) != BARCA_ID)
                
                score_barca = int(t_barca.get('score', -1))
                score_rival = int(t_rival.get('score', -1))
                
                # Se o placar for 0 ou mais, o jogo provavelmente ocorreu
                if score_barca >= 0:
                    data = ev.get('date', 'Data s/n')
                    jogos_com_placar.append({
                        "data": data,
                        "placar": f"Barça {score_barca} x {score_rival} {t_rival['team']['displayName']}",
                        "total": score_barca + score_rival
                    })
            except: continue

        # Pega os últimos 5 que têm placar
        ultimos = jogos_com_placar[-5:]
        
        if not ultimos:
            print("⚠️ Nenhum jogo com placar encontrado. Mostrando estrutura do 1º evento:")
            print(json.dumps(eventos[0], indent=2))
            return

        print("\n✅ JOGOS ENCONTRADOS:")
        for j in ultimos:
            print(f"📅 {j['data']} | {j['placar']} (Total: {j['total']})")

    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    auditoria_bruta_barca()
    
