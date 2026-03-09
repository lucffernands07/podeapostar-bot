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
    payload = {
        "chat_id": CHAT_ID, 
        "text": msg, 
        "parse_mode": "Markdown", 
        "disable_web_page_preview": True
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        print(f"📡 Status Telegram: {r.status_code}")
    except: 
        print("❌ Erro ao enviar para o Telegram")

def analisar_estatisticas(h2h_data):
    if not h2h_data or len(h2h_data) == 0: 
        return None
    
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
    
    # --- DICIONÁRIO DE LIGAS COM TEMPORADA CORRETA ---
    # Estrutura: ID: (Nome, Temporada)
    ligas_config = {
        # Europa (Ainda na 2025)
        39: ("Premier League", 2025), 
        140: ("LALIGA", 2025), 
        78: ("Bundesliga", 2025), 
        135: ("Serie A", 2025),
        61: ("Ligue 1", 2025), 
        94: ("Português", 2025), 
        88: ("Holandês", 2025), 
        2: ("Champions", 2025), 
        3: ("Europa League", 2025),
        
        # América do Sul / Brasil (Já na 2026)
        71: ("Brasileirão A", 2026), 
        72: ("Brasileirão B", 2026), 
        13: ("Libertadores", 2026),
        11: ("Sudamericana", 2026), 
        144: ("Copa do Brasil", 2026), 
        471: ("Paulistão", 2026), 
        472: ("Carioca", 2026)
    }
    
    jogos_selecionados = []
    print(f"🚀 Iniciando Varredura em {len(ligas_config)} ligas para {hoje}...")

    for l_id, (l_nome, season) in ligas_config.items():
        url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={hoje}&league={l_id}&season={season}"
        try:
            res = requests.get(url, headers=HEADERS, timeout=15).json()
            matches = res.get('response', [])
            
            if matches:
                print(f"✅ {len(matches)} jogos encontrados na {l_nome}")
                
                for item in matches:
                    t1 = item['teams']['home']
                    t2 = item['teams']['away']
                    hora = item['fixture']['date'][11:16]
                    
                    # Busca H2H (Últimos 8 confrontos diretos)
                    url_h2h = f"https://api-football-v1.p.rapidapi.com/v3/fixtures/headtohead?h2h={t1['id']}-{t2['id']}"
                    h2h_res = requests.get(url_h2h, headers=HEADERS, timeout=15).json()
                    stats = analisar_estatisticas(h2h_res.get('response', [])[:8])

                    if stats:
                        # Lógica Hierárquica 1.5 vs 0.5
                        mercado = ""
                        if stats['o15'] >= 85:
                            mercado = "⚽ +1.5 Gols — [Confiança]"
                        elif stats['o15'] >= 65:
                            mercado = "🛡️ +0.5 Gols — [Segurança]"
                        
                        # Mercados Adicionais
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
        except Exception as e:
            print(f"❌ Erro na liga {l_nome}: {e}")
            continue

    if jogos_selecionados:
        # Ordena pela força do 1.5 e pega os 10 melhores
        jogos_selecionados.sort(key=lambda x: x['forca'], reverse=True)
        final_list = jogos_selecionados[:10]
        
        mensagem = f"🎯 *BILHETE DO DIA ({len(final_list)} JOGOS)*\n💰🍀 BOA SORTE!!!\n\n"
        for i, jogo in enumerate(final_list, 1):
            mensagem += f"{i}. {jogo['texto']}\n\n"
        
        mensagem += "---\n🤖 *Análise: 1.5, 2.5, BTTS e Cantos*"
        enviar_telegram(mensagem)
    else:
        print("⚠️ Nenhum jogo aprovado pelos critérios hoje.")

if __name__ == "__main__":
    asyncio.run(executar_robo())
    
