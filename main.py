import os
import asyncio
import requests
import re
from datetime import datetime
from bs4 import BeautifulSoup

# --- CONFIGURAÇÃO --- #
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
ZENROWS_KEY = os.getenv('ZENROWS_KEY')

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": True}
    try:
        requests.post(url, json=payload, timeout=15)
    except: print("❌ Erro Telegram")

def extrair_valor_footy(texto_completo, mercado):
    padrao = r'(\d+)%\s*' + re.escape(mercado)
    match = re.search(padrao, texto_completo, re.IGNORECASE)
    if not match:
        padrao_inv = re.escape(mercado) + r'.*?(\d+)%'
        match = re.search(padrao_inv, texto_completo, re.IGNORECASE | re.DOTALL)
    return int(match.group(1)) if match else 0

async def analisar_no_footystats(t1_nome, t2_nome):
    # Transforma nomes para o padrão da URL do FootyStats
    t1 = t1_nome.lower().replace(" ", "-")
    t2 = t2_nome.lower().replace(" ", "-")
    url_footy = f"https://footystats.org/brazil/{t1}-vs-{t2}-h2h-stats" # O robô tentará adaptar a liga dinamicamente se necessário
    
    params = {'url': url_footy, 'apikey': ZENROWS_KEY, 'js_render': 'true', 'premium_proxy': 'true', 'wait_for': '.stat-strong', 'wait': '3000'}
    
    try:
        # Nota: Como o FootyStats muda a URL por liga, aqui usamos uma lógica de busca ou tentativa
        response = requests.get('https://api.zenrows.com/v1/', params=params, timeout=30)
        if response.status_code != 200: return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        texto = soup.get_text(separator=" ", strip=True).upper()
        
        return {
            "o15": extrair_valor_footy(texto, "OVER 1.5"),
            "o25": extrair_valor_footy(texto, "OVER 2.5"),
            "btts": extrair_valor_footy(texto, "BTTS"),
            "url": url_footy
        }
    except: return None

async def executar_robo():
    hoje = datetime.now().strftime("%Y%m%d")
    ligas_config = {"eng.1": "Premier League", "esp.1": "LALIGA", "ger.1": "Bundesliga", "ita.1": "Serie A", "fra.1": "Ligue 1", "bra.1": "Brasileirão A"}
    
    jogos_selecionados = []
    
    for l_id, l_nome in ligas_config.items():
        print(f"🌍 Buscando jogos em {l_nome}...")
        url_api = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{l_id}/scoreboard?dates={hoje}"
        try:
            res = requests.get(url_api, timeout=10).json()
            for ev in res.get('events', []):
                if ev.get('status', {}).get('type', {}).get('state') == 'pre':
                    c = ev['competitions'][0]['competitors']
                    t1, t2 = c[0]['team'], c[1]['team']
                    hora = ev['date'][11:16]
                    
                    # MOTOR FOOTYSTATS
                    stats = await analisar_no_footystats(t1['shortDisplayName'], t2['shortDisplayName'])
                    
                    if stats:
                        mercado = ""
                        # REGRA 1.5 vs 0.5 + BTTS + 2.5
                        if stats['o15'] >= 90:
                            mercado = "⚽ +1.5 Gols — [Confiança Máxima]"
                        elif stats['o15'] >= 70:
                            mercado = "🛡️ +0.5 Gols — [Segurança Ativada]"
                        elif stats['btts'] >= 80:
                            mercado = "🤝 Ambas Marcam — [4/5 Est.]"
                        elif stats['o25'] >= 75:
                            mercado = "⚡ +2.5 Gols — [Ataque Total]"
                        
                        if mercado:
                            jogos_selecionados.append({
                                "liga": l_nome,
                                "texto": f"🏟️ {t1['displayName']} x {t2['displayName']}\n🕒 {hora} | {l_nome}\n🎯 {mercado}\n📊 [Stats]({stats['url']})",
                                "forca": stats['o15']
                            })
        except: continue

    if jogos_selecionados:
        # Ordena pelos jogos com maior probabilidade de gols e pega os 10 melhores
        jogos_selecionados.sort(key=lambda x: x['forca'], reverse=True)
        final_list = jogos_selecionados[:10]
        
        mensagem = f"🎯 *BILHETE DO DIA ({len(final_list)} JOGOS)*\n💰🍀 BOA SORTE!!!\n\n"
        for i, jogo in enumerate(final_list, 1):
            mensagem += f"{i}. {jogo['texto']}\n\n"
        
        mensagem += "---\nAPOSTAR COM: 💸 [Bet365](https://www.bet365.com) | [Betano](https://www.betano.com)"
        enviar_telegram(mensagem)

if __name__ == "__main__":
    asyncio.run(executar_robo())
    
