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
    # Adicionamos 'gols_sofridos' para a trava do Ambas Marcam
    dados = {
        "gols_marcados": 0, 
        "gols_sofridos": 0,
        "over25_count": 0, 
        "btts_count": 0, 
        "jogos_com_gol_sofrido": 0,
        "marcou_nos_ultimos_2": True
    }
    
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
                    dados["gols_sofridos"] += gr
                    if (gm + gr) >= 3: dados["over25_count"] += 1
                    if gm > 0 and gr > 0: dados["btts_count"] += 1
                    if gr > 0: dados["jogos_com_gol_sofrido"] += 1
                    # Trava de momento: Não marcou em nenhum dos 2 últimos jogos
                    if i < 2 and gm == 0: 
                        dados["marcou_nos_ultimos_2"] = False
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
            "bel.1": "Belga", "bra.1": "Brasileirão A", "bra.2": "Brasileirão B",
            "bra.camp.carioca": "Carioca", "bra.camp.gaucho": "Gauchão",
            "bra.camp.mineiro": "Mineiro", "bra.camp.paulista": "Paulistão",
            "bra.copa_do_brasil": "Copa do Brasil", "bul.1": "Búlgaro",
            "conmebol.libertadores": "Libertadores", "conmebol.sudamericana": "Sul-Americana",
            "eng.1": "Premier League", "esp.1": "LALIGA", "fra.1": "Ligue 1",
            "ger.1": "Bundesliga", "ita.1": "Serie A", "ned.1": "Holandês",
            "por.1": "Português", "uefa.champions": "Champions"
        }
        
        jogos_selecionados = []
        vagas_25 = 2 
        vagas_btts = 3
        
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
                            # 1. ATROPELO: Exige histórico de gols alto e momento positivo
                            if vagas_25 > 0 and (d1['over25_count'] >= 4 and d1['gols_marcados'] >= 6) or (d2['over25_count'] >= 4 and d2['gols_marcados'] >= 6):
                                mercado = "⚡ +2.5 Gols — [Atropelo]"
                                vagas_25 -= 1
                            
                            # 2. AMBAS MARCAM: Trava de vulnerabilidade (ambos devem sofrer gols com frequência)
                            elif vagas_btts > 0 and (d1['btts_count'] >= 4 and d2['btts_count'] >= 4) and (d1['jogos_com_gol_sofrido'] >= 3 and d2['jogos_com_gol_sofrido'] >= 3):
                                mercado = "🤝 Ambas Marcam — [4/5 (Est.)]"
                                vagas_btts -= 1
                            
                            # 3. +1.5 GOLS: Trava de momento (não pode vir de 2 jogos secos)
                            elif d1['marcou_nos_ultimos_2'] and d2['marcou_nos_ultimos_2']:
                                mercado = "⚽ +1.5 Gols — [4/5 (Est.)]"
                            
                            # 4. SEGURANÇA: Mínimo de gols marcados recentemente
                            elif d1['gols_marcados'] >= 3 or d2['gols_marcados'] >= 3:
                                mercado = "🛡️ +0.5 Gols (HT/FT) — [Segurança]"
                            
                            if mercado:
                                jogos_selecionados.append({
                                    "liga": l_nome,
                                    "texto": f"🏟️ {t1['displayName']} x {t2['displayName']}\n🕒 {hora} | {l_nome}\n🎯 {mercado}\n📊 [Estatísticas](https://www.espn.com.br/futebol/confronto/_/jogoId/{ev['id']})",
                                    "gols": d1['gols_marcados'] + d2['gols_marcados']
                                })
            except Exception as e:
                print(f"Erro na liga {l_nome}: {e}")
                continue

        await browser.close()

        if jogos_selecionados:
            # Pega os 10 com maior volume de gols histórico
            jogos_selecionados.sort(key=lambda x: x['gols'], reverse=True)
            final_list = jogos_selecionados[:10]
            
            # Organiza alfabeticamente por liga
            final_list.sort(key=lambda x: x['liga'])
            
            ligas_no_bilhete = sorted(list(set(j['liga'] for j in final_list)))
            total_jogos = len(final_list)
            
            mensagem = f"🎯 *BILHETE DO DIA ({total_jogos} JOGOS)*\n"
            mensagem += f"💰🍀 BOA SORTE!!!\n\n"
            
            mensagem += "🏟️ *LIGAS ENCONTRADAS:*\n"
            for liga in ligas_no_bilhete:
                mensagem += f"🔹 {liga}\n"
            
            mensagem += "\n"
            for i, jogo in enumerate(final_list, 1):
                mensagem += f"{i}. {jogo['texto']}\n\n"
            
            mensagem += "---\nAPOSTAR COM: 💸 [Bet365](https://www.bet365.com) | [Betano](https://www.betano.com)"
            
            enviar_telegram(mensagem)

if __name__ == "__main__":
    asyncio.run(executar_robo())
