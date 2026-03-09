import os
import asyncio
import requests
from datetime import datetime

# --- CONFIGURAÇÃO (Lidas do GitHub Secrets) --- #
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
API_KEY = os.getenv('X_RAPIDAPI_KEY') 
HOST = "api-football-v1.p.rapidapi.com"

HEADERS = {
    'x-rapidapi-host': HOST,
    'x-rapidapi-key': API_KEY
}

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": True}
    try:
        requests.post(url, json=payload, timeout=15)
    except: print("❌ Erro Telegram")

def analisar_estatisticas(h2h_data):
    if not h2h_data or len(h2h_data) == 0: return None
    
    total = len(h2h_data)
    o15, o25, btts = 0, 0, 0
    
    for game in h2h_data:
        gols_c = game['goals']['home'] or 0
        gols_f = game['goals']['away'] or 0
        soma = gols_c + gols_f
        
        if soma >= 2: o15 += 1
        if soma >= 3: o25 += 1
        if gols_c > 0 and gols_f > 0: btts += 1

    return {
        "o15": (o15 / total) * 100,
        "o25": (o25 / total) * 100,
        "btts": (btts / total) * 100
    }

async def executar_robo():
    hoje = datetime.now().strftime("%Y-%m-%d")
    ano_atual = datetime.now().year
    
    # --- SUAS LIGAS MAPEADAS ---
    ligas_config = {
        39: "Premier League", 140: "LALIGA", 78: "Bundesliga", 135: "Serie A",
        61: "Ligue 1", 71: "Brasileirão A", 72: "Brasileirão B", 94: "Português",
        88: "Holandês", 2: "Champions", 3: "Europa League", 13: "Libertadores",
        11: "Sudamericana", 144: "Copa do Brasil", 471: "Paulistão", 472: "Carioca"
    }
    
    jogos_selecionados = []
    print(f"🚀 Iniciando Varredura em {len(ligas_config)} ligas para a data {hoje}...")

    for l_id, l_nome in ligas_config.items():
        # Tentamos a temporada atual
        url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={ano_atual}"
        try:
            res = requests.get(url, headers=HEADERS, timeout=15).json()
            for item in res.get('response', []):
                t1 = item['teams']['home']
                t2 = item['teams']['away']
                hora = item['fixture']['date'][11:16]
                
                # Busca H2H (Últimos 8 jogos entre eles)
                url_h2h = f"https://api-football-v1.p.rapidapi.com/v3/fixtures/headtohead?h2h={t1['id']}-{t2['id']}"
                h2h_res = requests.get(url_h2h, headers=HEADERS, timeout=15).json()
                stats = analisar_estatisticas(h2h_res.get('response', [])[:8])

                if stats:
                    mercado = ""
                    if stats['o15'] >= 85:
                        mercado = "⚽ +1.5 Gols — [Confiança]"
                    elif stats['o15'] >= 65:
                        mercado = "🛡️ +0.5 Gols — [Segurança]"
                    
                    extras = []
                    if stats['o25'] >= 70: extras.append("⚡ +2.5")
                    if stats['btts'] >= 75: extras.append("🤝 BTTS")
                    if stats['o15'] > 80: extras.append("🚩 +8.5 Cantos")
                    
                    if mercado:
                        detalhes = f" ({' | '.join(extras)})" if extras else ""
                        jogos_selecionados.append({
                            "liga": l_nome,
                            "texto": f"🏟️ *{t1['name']} x {t2['name']}*\n🕒 {hora} | {l_nome}\n🎯 {mercado}{detalhes}",
                            "forca": stats['o15']
                        })
        except: continue

    if jogos_selecionados:
        jogos_selecionados.sort(key=lambda x: x['forca'], reverse=True)
        final_list = jogos_selecionados[:10]
        
        mensagem = f"🎯 *BILHETE DO DIA ({len(final_list)} JOGOS)*\n💰🍀 BOA SORTE!!!\n\n"
        for i, jogo in enumerate(final_list, 1):
            mensagem += f"{i}. {jogo['texto']}\n\n"
        
        mensagem += "---\n🤖 *Análise Profissional (Gols, BTTS e Cantos)*"
        enviar_telegram(mensagem)
    else:
        print("⚠️ Nenhum jogo encontrado para as regras hoje.")

if __name__ == "__main__":
    asyncio.run(executar_robo())
        
