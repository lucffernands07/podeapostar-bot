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
        "disable_web_page_preview": True  # Evita que o Telegram crie previews gigantes dos links
    }
    try:
        requests.post(url, json=payload, timeout=15)
    except:
        print("❌ Erro ao enviar mensagem para o Telegram.")

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
            "esp.1": "LaLiga", "eng.1": "Premier League", "ger.1": "Bundesliga", "ita.1": "Serie A",
            "fra.1": "Ligue 1", "ned.1": "Holanda", "bul.1": "Bulgária", "por.1": "Portugal",
            "bra.1": "Série A", "bra.2": "Série B", "bra.camp.paulista": "Paulistão",
            "bra.camp.carioca": "Carioca", "bra.camp.mineiro": "Mineiro", "bra.camp.gaucho": "Gaúcho",
            "uefa.champions": "Champions", "conmebol.libertadores": "Libertadores"
        }
        
        jogos_por_liga = {}
        vagas_25 = 1
        vagas_btts = 3
        
        # 1. Coleta e processamento
        for l_id, l_nome in ligas_config.items():
            print(f"🌍 Verificando {l_nome}...")
            url_api = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{l_id}/scoreboard?dates={hoje}"
            try:
                res = requests.get(url_api, timeout=10).json()
                for ev in res.get('events', []):
                    if ev.get('status', {}).get('type', {}).get('state') == 'pre':
                        c = ev['competitions'][0]['competitors']
                        t1, t2 = c[0]['team'], c[1]['team']
                        hora = ev['date'][11:16] # Extrai HH:MM do ISO
                        
                        d1 = await extrair_dados_detalhados(browser, t1['id'])
                        d2 = await extrair_dados_detalhados(browser, t2['id'])
                        
                        if d1 and d2:
                            # Decisão de Mercado
                            mercado = ""
                            if vagas_25 > 0 and ((d1['over25_count'] >= 4 or d1['gols_marcados'] >= 8) or (d2['over25_count'] >= 4 or d2['gols_marcados'] >= 8)):
                                mercado = "🎯 🔥 +2.5 GOLS"
                                vagas_25 -= 1
                            elif vagas_btts > 0 and (d1['btts_count'] >= 4 and d2['btts_count'] >= 4):
                                mercado = "🎯 🤝 AMBAS MARCAM"
                                vagas_btts -= 1
                            elif d1['ultimos_3_marcou'] and d2['ultimos_3_marcou']:
                                mercado = "🎯 ⚽ +1.5 GOLS"
                            elif d1['gols_marcados'] >= 3 or d2['gols_marcados'] >= 3:
                                mercado = "🎯 🛡️ +0.5 GOLS"
                            
                            if mercado:
                                item = (f"🏟️ *{t1['displayName']} x {t2['displayName']}*\n"
                                        f"🕒 {hora} | {mercado}\n"
                                        f"📈 [Estatísticas](https://www.espn.com.br/futebol/confronto/_/jogoId/{ev['id']})\n"
                                        f"🔗 [Betano](https://www.betano.com) | [Bet365](https://www.bet365.com)\n")
                                
                                if l_nome not in jogos_por_liga:
                                    jogos_por_liga[l_nome] = []
                                jogos_por_liga[l_nome].append(item)
            except: continue

        await browser.close()

        # 2. Formatação da Mensagem Final
        if jogos_por_liga:
            mensagem = "🏆 *BILHETE DO DIA (SISTEMA HÍBRIDO)*\n"
            mensagem += "Ligas analisadas: " + ", ".join(sorted(ligas_config.values())) + "\n\n"
            
            # Ordenação Alfabética das Ligas
            for liga in sorted(jogos_por_liga.keys()):
                mensagem += f"📍 *{liga.upper()}*\n"
                mensagem += "\n".join(jogos_por_liga[liga]) + "\n"
            
            enviar_telegram(mensagem)

if __name__ == "__main__":
    asyncio.run(executar_robo())
