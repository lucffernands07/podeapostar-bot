import os
import asyncio
import requests
from datetime import datetime
from playwright.async_api import async_playwright

# --- CONFIGURAÇÃO --- #
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, json=payload, timeout=15)
    except:
        print("❌ Erro ao enviar para o Telegram.")

async def extrair_dados_detalhados(browser, team_id):
    page = await browser.new_page()
    url = f"https://www.espn.com.br/futebol/time/resultados/_/id/{team_id}"
    dados = {"gols_marcados": 0, "over25_count": 0, "btts_count": 0, "ultimos_3_marcou": True}
    
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        rows = await page.query_selector_all(".Table__TR--sm")
        for i, row in enumerate(rows[:5]):
            cols = await row.query_selector_all("td")
            if len(cols) >= 3:
                txt = await cols[2].inner_text()
                placar = "".join([c for c in txt if c.isdigit() or c == "-"])
                if "-" in placar:
                    p = placar.split("-")
                    gm, gr = int(p[0][:1]), int(p[1][:1])
                    dados["gols_marcados"] += gm
                    if (gm + gr) >= 3: dados["over25_count"] += 1
                    if gm > 0 and gr > 0: dados["btts_count"] += 1
                    if i < 3 and gm == 0: dados["ultimos_3_marcou"] = False
        await page.close()
        return dados
    except:
        await page.close()
        return None

async def executar_robo():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        hoje = datetime.now().strftime("%Y%m%d")
        
        ligas_config = {
            "bel.1": "Belga",
            "bra.1": "Brasileirão A",
            "bra.2": "Brasileirão B",
            "bra.camp.carioca": "Carioca",
            "bra.camp.gaucho": "Gauchão",
            "bra.camp.mineiro": "Mineiro",
            "bra.camp.paulista": "Paulistão",
            "bra.copa_do_brasil": "Copa do Brasil",
            "bul.1": "Búlgaro",
            "conmebol.libertadores": "Libertadores",
            "conmebol.sudamericana": "Sul-Americana",
            "eng.1": "Premier League",
            "esp.1": "LALIGA",
            "fra.1": "Ligue 1",
            "ger.1": "Bundesliga",
            "ita.1": "Serie A",
            "ned.1": "Holandês",
            "por.1": "Português",
            "uefa.champions": "Champions"
        }
        
        jogos_selecionados = []
        vagas_25 = 1
        vagas_btts = 3
        ligas_encontradas = set()
        
        for l_id, l_nome in ligas_config.items():
            print(f"🌍 Verificando {l_nome}...")
            url_api = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{l_id}/scoreboard?dates={hoje}"
            try:
                res = requests.get(url_api, timeout=10).json()
                for ev in res.get('events', []):
                    if ev.get('status', {}).get('type', {}).get('state') == 'pre':
                        c = ev['competitions'][0]['competitors']
                        t1, t2 = c[0]['team'], c[1]['team']
                        hora = ev['date'][11:16]
                        
                        d1 = await extrair_dados_detalhados(browser, t1['id'])
                        d2 = await extrair_dados_detalhados(browser, t2['id'])
                        
                        if d1 and d2:
                            mercado = ""
                            if vagas_25 > 0 and ((d1['over25_count'] >= 4 or d1['gols_marcados'] >= 8) or (d2['over25_count'] >= 4 or d2['gols_marcados'] >= 8)):
                                mercado = "⚡ +2.5 Gols — [Atropelo]"
                                vagas_25 -= 1
                            elif vagas_btts > 0 and (d1['btts_count'] >= 4 and d2['btts_count'] >= 4):
                                mercado = "🤝 Ambas Marcam — [4/5 (Est.)]"
                                vagas_btts -= 1
                            elif d1['ultimos_3_marcou'] and d2['ultimos_3_marcou']:
                                mercado = "⚽ +1.5 Gols — [4/5 (Est.)]"
                            elif d1['gols_marcados'] >= 3 or d2['gols_marcados'] >= 3:
                                mercado = "🛡️ +0.5 Gols (HT/FT) — [Segurança]"
                            
                            if mercado:
                                ligas_encontradas.add(l_nome)
                                jogos_selecionados.append({
                                    "texto": f"🏟️ {t1['displayName']} x {t2['displayName']}\n🕒 {hora} | {l_nome}\n🎯 {mercado}\n📊 [Estatísticas](https://www.espn.com.br/futebol/confronto/_/jogoId/{ev['id']})",
                                    "gols": d1['gols_marcados'] + d2['gols_marcados']
                                })
            except Exception as e:
                print(f"Erro na liga {l_nome}: {e}")
                continue

        await browser.close()

        if jogos_selecionados:
            jogos_selecionados.sort(key=lambda x: x['gols'], reverse=True)
            final_list = jogos_selecionados[:10]
            total_jogos = len(final_list)
            
            mensagem = f"🎯 *BILHETE CALIBRADO ({total_jogos} JOGOS)*\n"
            mensagem += f"💰 ODD ESTIMADA: Variação das Casas\n\n"
            
            mensagem += "🏟️ *LIGAS ENCONTRADAS:*\n"
            for liga in sorted(list(ligas_encontradas)):
                mensagem += f"🔹 {liga}\n"
            
            mensagem += "\n"
            for i, jogo in enumerate(final_list, 1):
                mensagem += f"{i}. {jogo['texto']}\n\n"
            
            mensagem += "---\nAPOSTAR COM: 💸 [Bet365](https://www.bet365.com) | [Betano](https://www.betano.com)"
            
            enviar_telegram(mensagem)

if __name__ == "__main__":
    asyncio.run(executar_robo())
        
