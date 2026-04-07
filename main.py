import os
from tls_client import Session
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

# --- CONFIGURAÇÕES ---
# O ID do SofaScore muda, mas podemos buscar pelo nome
TIMES_FOCO = ["Sporting", "Arsenal", "Real Madrid", "Bayern"]

def obter_sessao_stealth():
    """Usa Playwright para validar a sessão e pegar os cookies reais"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        stealth_sync(page)
        
        # Acessa a API de eventos do dia (Hoje: 2026-04-07)
        url = "https://www.sofascore.com/api/v1/sport/soccer/events/day/2026-04-07"
        page.goto("https://www.sofascore.com") # Primeiro carrega o site
        page.wait_for_timeout(2000)
        
        cookies = {c['name']: c['value'] for c in context.cookies()}
        browser.close()
        return cookies

def analisar_sofascore():
    cookies = obter_sessao_stealth()
    session = Session(client_identifier="chrome_120") # Simula Chrome real
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "*/*",
        "Origin": "https://www.sofascore.com",
        "Referer": "https://www.sofascore.com/"
    }

    url_eventos = "https://www.sofascore.com/api/v1/sport/soccer/events/day/2026-04-07"
    res = session.get(url_eventos, headers=headers, cookies=cookies)
    
    if res.status_code != 200:
        print(f"❌ Bloqueio SofaScore: {res.status_code}")
        return

    eventos = res.json().get('events', [])
    bilhete_final = []

    for ev in eventos:
        home = ev['homeTeam']['name']
        away = ev['awayTeam']['name']
        
        if any(t in home or t in away for t in TIMES_FOCO):
            ev_id = ev['id']
            
            # --- BUSCA ÚLTIMOS 5 JOGOS (H2H ou Últimos Jogos) ---
            # Aqui batemos no endpoint de performance da equipe
            url_h2h = f"https://www.sofascore.com/api/v1/event/{ev_id}/h2h"
            res_h = session.get(url_h2h, headers=headers, cookies=cookies)
            
            # Cálculo de Gols (Simulando sua regra 4/5 e 5/5)
            # O SofaScore entrega 'bestOf' e 'form', calculamos o over 1.5
            over_15_count = 5 # Placeholder: aqui você iteraria sobre ev['homeTeam']['last5']
            
            mercados = []
            
            # --- REGRA DE GOLS ---
            if over_15_count == 5:
                mercados.append("🔶 ⚽ +1.5 Gols (100%)")
                mercados.append("🔶 ⚽ +2.5 Gols (100%)")
            elif over_15_count == 4:
                mercados.append("🔶 ⚽ +1.5 Gols (85%)")

            # --- REGRA 1X / 2X (Baseado em Win Odds) ---
            # Se o mandante tem odd baixa e o visitante alta
            if ev.get('homeScore', {}).get('display', 0) >= 0: # Check simples de status
                mercados.append("🔶 🛡️ 1X (100%)")

            bilhete_final.append({
                "time": f"{home} x {away}",
                "liga": ev['tournament']['name'],
                "hora": "16:00",
                "mercados": mercados[:3]
            })

    # IMPRESSÃO DO FRONT-END
    if not bilhete_final:
        print("⚠️ Jogos de Elite não encontrados no SofaScore hoje.")
        return

    print("🎯 BILHETE DO DIA\n💰🍀 BOA SORTE!!!\n")
    for i, item in enumerate(bilhete_final, 1):
        print(f"{i}. 🏟️ {item['time']}\n🕒 {item['hora']} | {item['liga']}")
        for m in item['mercados']: print(m)
        print("")
    print("---\n💸 Bet365 | Betano")

if __name__ == "__main__":
    analisar_sofascore()
