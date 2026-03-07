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
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=15)
    except:
        print("❌ Erro ao enviar mensagem para o Telegram.")

async def extrair_dados_detalhados(browser, team_id):
    """Abre o HTML para garantir que Barcelona e outros times não venham vazios"""
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
                    # Pega o primeiro dígito para evitar erros de placar agregado (ex: 3-04-3)
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
        
        # --- DICIONÁRIO COMPLETO DE LIGAS (Big 5, Holanda, Bulgária e Estaduais) ---
        ligas = {
            "esp.1": "LaLiga", "eng.1": "Premier", "ger.1": "Bundes", "ita.1": "Serie A",
            "fra.1": "Ligue 1", "ned.1": "Holanda", "bul.1": "Bulgária", "por.1": "Portugal",
            "bra.1": "Série A", "bra.2": "Série B", "bra.camp.paulista": "Paulistão",
            "bra.camp.carioca": "Carioca", "bra.camp.mineiro": "Mineiro", "bra.camp.gaucho": "Gaúcho",
            "uefa.champions": "Champions", "conmebol.libertadores": "Liberta"
        }
        
        jogos_analisados = []
        for l_id, l_nome in ligas.items():
            print(f"🌍 Verificando {l_nome}...")
            url_api = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{l_id}/scoreboard?dates={hoje}"
            try:
                res = requests.get(url_api, timeout=10).json()
                for ev in res.get('events', []):
                    if ev.get('status', {}).get('type', {}).get('state') == 'pre':
                        c = ev['competitions'][0]['competitors']
                        t1, t2 = c[0]['team'], c[1]['team']
                        d1 = await extrair_dados_detalhados(browser, t1['id'])
                        d2 = await extrair_dados_detalhados(browser, t2['id'])
                        if d1 and d2:
                            jogos_analisados.append({"t1": t1['displayName'], "t2": t2['displayName'], "d1": d1, "d2": d2})
            except: continue

        # --- LÓGICA DE SELEÇÃO E LIMITADORES ---
        bilhete = []
        vagas_25 = 1
        vagas_btts = 3
        
        # Prioriza jogos com maior volume de gols para as primeiras vagas
        jogos_analisados.sort(key=lambda x: x['d1']['gols_marcados'] + x['d2']['gols_marcados'], reverse=True)

        for j in jogos_analisados:
            t_nome = f"🏟️ *{j['t1']} x {j['t2']}*"
            d1, d2 = j['d1'], j['d2']

            # 1. REGRA +2.5 (MAX 1 - Apenas um time precisa 4/5 ou 8+ gols)
            if vagas_25 > 0 and ((d1['over25_count'] >= 4 or d1['gols_marcados'] >= 8) or (d2['over25_count'] >= 4 or d2['gols_marcados'] >= 8)):
                bilhete.append(f"{t_nome}\n🎯 🔥 *+2.5 GOLS*")
                vagas_25 -= 1
                continue

            # 2. REGRA AMBAS MARCAM (MAX 3 - Precisa 4/5 NOS DOIS)
            if vagas_btts > 0 and (d1['btts_count'] >= 4 and d2['btts_count'] >= 4):
                bilhete.append(f"{t_nome}\n🎯 🤝 *AMBAS MARCAM*")
                vagas_btts -= 1
                continue

            # 3. REGRA +1.5 (Sem 0 gols nos últimos 3 de cada time)
            if d1['ultimos_3_marcou'] and d2['ultimos_3_marcou']:
                bilhete.append(f"{t_nome}\n🎯 ⚽ *+1.5 GOLS*")
                continue

            # 4. REGRA +0.5 (Segurança 3/5)
            if d1['gols_marcados'] >= 3 or d2['gols_marcados'] >= 3:
                bilhete.append(f"{t_nome}\n🎯 🛡️ *+0.5 GOLS*")

        await browser.close()
        if bilhete:
            enviar_telegram("🏆 *BILHETE DO DIA (SISTEMA HÍBRIDO)*\n\n" + "\n\n".join(bilhete[:10]))

if __name__ == "__main__":
    asyncio.run(executar_robo())
        
