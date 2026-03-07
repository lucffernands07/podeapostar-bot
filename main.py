import requests
from datetime import datetime, timedelta

HEADERS = {"User-Agent": "Mozilla/5.0"}
BARCA_ID = "83"

def auditoria_real_liga():
    print(f"🔎 BUSCANDO HISTÓRICO REAL NA LALIGA - BARCELONA (ID: {BARCA_ID})")
    print("-" * 50)
    
    gols_feitos = 0
    jogos_25 = 0
    jogos_encontrados = 0
    
    # Vamos voltar 20 dias no calendário da liga para achar os últimos 5 jogos
    for i in range(1, 21):
        data_busca = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/scoreboard?dates={data_busca}"
        
        try:
            res = requests.get(url, headers=HEADERS, timeout=5).json()
            for ev in res.get('events', []):
                teams = ev.get('competitions', [{}])[0].get('competitors', [])
                
                if any(str(t['id']) == BARCA_ID for t in teams):
                    t_alvo = next(t for t in teams if str(t['id']) == BARCA_ID)
                    t_rival = next(t for t in teams if str(t['id']) != BARCA_ID)
                    
                    gf = int(t_alvo.get('score', 0))
                    gr = int(t_rival.get('score', 0))
                    jogos_encontrados += 1
                    gols_feitos += gf
                    if (gf + gr) >= 3: jogos_25 += 1
                    
                    print(f" ✅ Jogo {jogos_encontrados}: Barça {gf} x {gr} {t_rival['team']['displayName']} ({data_busca})")
                    
                    if jogos_encontrados >= 5: break
            if jogos_encontrados >= 5: break
        except: continue

    print("-" * 50)
    if jogos_encontrados > 0:
        print(f"📊 RESULTADO PARA O BILHETE:")
        print(f"   - Gols Marcados (Últimos 5): {gols_feitos}")
        print(f"   - Frequência +2.5 Gols: {jogos_25}/5")
        
        if gols_feitos >= 8 or jogos_25 >= 4:
            print("\n🔥 STATUS: ATROPELO CONFIRMADO! Mercado: +2.5 Gols")
        else:
            print("\n⚽ STATUS: NORMAL. Mercado: +1.5 Gols")
    else:
        print("❌ Não foi possível encontrar jogos no calendário da liga.")

if __name__ == "__main__":
    auditoria_real_liga()
                       
