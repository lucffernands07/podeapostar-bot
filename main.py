import os
import requests
import random
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": mensagem, 
        "parse_mode": "Markdown", 
        "disable_web_page_preview": "true"
    }
    try:
        requests.post(url, json=payload, timeout=15)
    except:
        pass

def formatar_horario(data_iso):
    try:
        data_limpa = data_iso.replace('Z', '')
        dt_utc = datetime.fromisoformat(data_limpa)
        dt_br = dt_utc - timedelta(hours=3) # Horário de Brasília
        return dt_br.strftime("%H:%M")
    except:
        return "Horário a definir"

def definir_palpite_estrategico():
    """
    Retorna palpite, Confiança e Odd Estimada.
    """
    opcoes = [
        ("⚽ +1.5 Gols na Partida", 82, 1.45),
        ("⚽ +2.5 Gols na Partida", 70, 1.90),
        ("🎯 Ambas Marcam - Sim", 75, 1.80),
        ("🛡️ Empate Anula Fav.", 85, 1.40),
        ("🔥 Casa ou Fora (12)", 78, 1.35),
        ("⚽ +0.5 Gols (Base Segura)", 94, 1.10)
    ]
    return random.choice(opcoes)

def executar_robo():
    print(f"[{datetime.now().strftime('%H:%M')}] Buscando bilhete calibrado (Odd 90-110)...")
    
    ligas = {
        "bra.1": "Série A Brasil", "bra.2": "Série B Brasil", "bra.copa_do_brasil": "Copa do Brasil",
        "bra.camp_paulista": "Paulistão", "bra.camp_carioca": "Cariocão",
        "conmebol.libertadores": "Libertadores", "conmebol.sudamericana": "Sul-Americana",
        "eng.1": "Premier League (Ing)", "esp.1": "LaLiga (Esp)", "esp.copa_del_rey": "Copa del Rey (Esp)",
        "ita.1": "Série A (Ita)", "ita.coppa_italia": "Coppa Italia (Ita)", "ger.1": "Bundesliga (Ale)",
        "por.1": "Liga Portugal (Por)", "uefa.champions": "Champions League",
        "ned.1": "Eredivisie (Hol)", "aut.1": "Bundesliga (Aut)", "bel.1": "Pro League (Bel)", "usa.1": "MLS (EUA)"
    }

    jogos_disponiveis = []

    for liga_id, liga_nome in ligas.items():
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{liga_id}/scoreboard"
        try:
            res = requests.get(url, timeout=15)
            data = res.json()
            eventos = data.get('events', [])
            for evento in eventos:
                nome_bruto = evento.get('name')
                nome_jogo = nome_bruto.replace(' at ', ' x ').replace(' & ', ' x ')
                jogos_disponiveis.append({
                    "liga": liga_nome,
                    "jogo": nome_jogo,
                    "hora": formatar_horario(evento.get('date')),
                    "link": evento.get('links')[0].get('href')
                })
        except:
            continue

    if len(jogos_disponiveis) < 10:
        print("Poucos jogos disponíveis para montar a múltipla.")
        return

    # --- LOOP DE CALIBRAGEM ---
    # O robô tentará 500 combinações diferentes até achar uma com odd entre 90 e 110
    tentativas = 0
    while tentativas < 500:
        selecao = random.sample(jogos_disponiveis, 10)
        odd_total = 1.0
        bilhete_final = []

        for jogo in selecao:
            palpite, conf, odd_est = definir_palpite_estrategico()
            odd_total *= odd_est
            bilhete_final.append({**jogo, "aposta": palpite, "conf": conf, "odd": odd_est})

        # Verifica se a odd está no intervalo desejado
        if 90 <= odd_total <= 110:
            msg = f"🎯 *BILHETE CALIBRADO: ODD {odd_total:.2f}*\n_Alvo: Multiplicação entre 90x e 110x | {datetime.now().strftime('%d/%m')}_\n\n"
            
            for i, j in enumerate(bilhete_final, 1):
                msg += f"{i}. 🏟️ *{j['jogo']}*\n🕒 {j['hora']} | _{j['liga']}_\n🎯 *{j['aposta']}* (Odd ~{j['odd']})\n\n"
            
            msg += f"📊 [Analisar Todos no ESPN]({bilhete_final[0]['link']})\n\n⚠️ _Odds estimadas. Confira no seu site de apostas._"
            
            enviar_telegram(msg)
            print(f"Sucesso! Bilhete com Odd {odd_total:.2f} enviado após {tentativas} tentativas.")
            return
        
        tentativas += 1

    print("Não foi possível encontrar uma combinação exata no intervalo 90-110.")

if __name__ == "__main__":
    executar_robo()
    
