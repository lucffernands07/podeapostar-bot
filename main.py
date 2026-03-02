import os
import requests
from bs4 import BeautifulSoup
import time

# Configurações do Telegram vindas dos Secrets do GitHub
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={mensagem}&parse_mode=Markdown"
    try:
        requests.get(url)
    except Exception as e:
        print(f"Erro ao enviar: {e}")

def analisar_detalhes(url_jogo):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url_jogo, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        texto_pagina = soup.get_text().lower()

        # --- LÓGICA DE ESCALAÇÃO ---
        status_time = "✅ Titulares Prováveis"
        # Termos em português e inglês para cobrir as ligas internacionais
        termos_alerta = ["reserva", "poupado", "desfalques", "injury", "substitute", "ausentes"]
        if any(word in texto_pagina for word in termos_alerta):
            status_time = "⚠️ Atenção: Possíveis Desfalques!"

        # --- LÓGICA DE GOLS (HISTÓRICO H2H) ---
        placares = [p.text.strip() for p in soup.find_all('span', class_='score')]
        total_jogos = len(placares)
        gols_no_range = 0
        
        for p in placares:
            try:
                # Soma os gols do placar (ex: "2-1" vira 3)
                gols = sum(map(int, p.split('-')))
                # Verifica se está no padrão de 1 a 3 gols
                if 1 <= gols <= 3:
                    gols_no_range += 1
            except:
                continue
        
        prob = (gols_no_range / total_jogos) if total_jogos > 0 else 0
        return prob, status_time
    except:
        return 0, "❌ Erro na análise detalhada"

def executar_robo():
    enviar_telegram("🌍 *PodeApostar_Bot:* Varredura (BRA, ING, ITA, ESP, POR) Iniciada!")
    
    url_base = "https://www.placardefutebol.com.br"
    # Lista atualizada com 5 ligas
    ligas = [
        "/brasileirao-serie-a",
        "/campeonato-ingles",
        "/campeonato-italiano",
        "/campeonato-espanhol",
        "/campeonato-portugues"
    ]
    
    total_encontrados = 0

    for liga in ligas:
        try:
            response = requests.get(url_base + liga, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', href=True)

            for link in links:
                if '/jogo/' in link['href']:
                    times = link.find_all('span', class_='team-name')
                    if len(times) < 2: continue
                    
                    casa, fora = times[0].text, times[1].text
                    prob, status = analisar_detalhes(url_base + link['href'])
                    
                    # FILTRO DE SENSIBILIDADE EM 0.4 (40%)
                    if prob >= 0.4:
                        # --- DEFINIÇÃO DA SUGESTÃO DE ENTRADA ---
                        if prob >= 0.7:
                            sugestao = "🔥 *FORTE:* Mínimo 2 Gols (Over 1.5)"
                        elif prob >= 0.5:
                            sugestao = "✅ *PADRÃO:* Mercado 1-3 Gols"
                        else:
                            sugestao = "⚠️ *MÍNIMO:* Mínimo 1 Gol (Over 0.5)"

                        msg = (f"🏆 *{liga.replace('/','').upper()}*\n"
                               f"🏟️ {casa} x {fora}\n"
                               f"📈 Tendência: {prob*100:.0f}%\n"
                               f"📋 Info: {status}\n"
                               f"🎯 Sugestão: {sugestao}\n"
                               f"⏱️ Estratégia: Buscar Gol no HT")
                        
                        enviar_telegram(msg)
                        total_encontrados += 1
                    
                    # Pausa curta para evitar bloqueio do servidor
                    time.sleep(1)
        except Exception as e:
            print(f"Erro ao processar liga {liga}: {e}")
            continue

    if total_encontrados == 0:
        enviar_telegram("🔍 *Checking:* Sem padrões claros de gols encontrados nas ligas monitoradas hoje.")

if __name__ == "__main__":
    executar_robo()
