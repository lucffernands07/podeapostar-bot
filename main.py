import requests

# --- CONFIGURAÇÃO --- #
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
BARCA_ID = "83"  # ID fixo do Barcelona na ESPN

def auditoria_barcelona():
    print(f"🔎 Iniciando Auditoria: BARCELONA (ID: {BARCA_ID})")
    print("-" * 50)
    
    try:
        # URL do Calendário (Aba de Estatísticas/Resultados)
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/teams/{BARCA_ID}/schedule"
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        
        # Filtra apenas jogos finalizados (status 'post')
        jogos_finalizados = [
            e for e in res.get('events', []) 
            if e.get('status', {}).get('type', {}).get('state') == 'post'
        ]
        
        ultimos_5 = jogos_finalizados[-5:]
        
        if not ultimos_5:
            print("❌ ERRO: Não foi possível encontrar jogos finalizados no calendário.")
            return

        gols_marcados = 0
        count_15 = 0
        count_25 = 0

        for i, ev in enumerate(ultimos_5, 1):
            comp = ev.get('competitions', [{}])[0]
            teams = comp.get('competitors', [])
            
            # Identifica o Barça e o Rival
            t_barca = next(t for t in teams if str(t['id']) == BARCA_ID)
            t_rival = next(t for t in teams if str(t['id']) != BARCA_ID)
            
            gm = int(t_barca.get('score', 0))
            gs = int(t_rival.get('score', 0))
            total_gols = gm + gs
            
            status_15 = "✅" if total_gols >= 2 else "❌"
            status_25 = "✅" if total_gols >= 3 else "❌"
            
            print(f" Jogo {i}: Barcelona {gm} x {gs} {t_rival['team']['displayName']}")
            print(f"         Total: {total_gols} gols | +1.5: {status_15} | +2.5: {status_25}")
            
            gols_marcados += gm
            if total_gols >= 2: count_15 += 1
            if total_gols >= 3: count_25 += 1

        print("-" * 50)
        print(f"📊 RESULTADO DA AUDITORIA:")
        print(f"   - Gols Marcados pelo Barça (5 jogos): {gols_marcados}")
        print(f"   - Frequência +1.5 Gols: {count_15}/5")
        print(f"   - Frequência +2.5 Gols: {count_25}/5")
        
        # Lógica de decisão do Robô
        if count_25 >= 4 or gols_marcados >= 8:
            print("\n🔥 CONCLUSÃO: Mercado indicado é +2.5 GOLS (ATROPELO)")
        elif count_15 >= 3:
            print("\n⚽ CONCLUSÃO: Mercado indicado é +1.5 GOLS")
        else:
            print("\n⚡ CONCLUSÃO: Mercado de Segurança")

    except Exception as e:
        print(f"❌ ERRO CRÍTICO NA EXTRAÇÃO: {e}")

if __name__ == "__main__":
    auditoria_barcelona()
        
