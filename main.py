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

def obter_data_hoje_br():
    # Retorna a data atual no fuso de Brasília (UTC-3)
    return (datetime.utcnow() - timedelta(hours=3)).strftime('%Y-%m-%d')

def formatar_horario_br(data_iso):
    try:
        data_limpa = data_iso.replace('Z', '')
        dt_utc = datetime.fromisoformat(data_limpa)
        dt_br = dt_utc - timedelta(hours=3)
        return dt_br.strftime("%H:%M")
    except:
        return "Horário a definir"

def definir_palpite_estrategico():
    # Mercado, Confiança, Odd Estimada
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
    hoje_br = obter_data_hoje_br()
    print(f"[{datetime.now().strftime('%H:%M')}] Filtrando jogos de HOJE ({hoje_br}) para Odd 90-110...")
    
    ligas = {
        "bra.1": "Série A Brasil", "bra.2": "Série B Brasil", "bra.copa_do_brasil": "Copa do Brasil",
        "bra.camp_paulista": "Paulistão", "bra.camp_carioca": "Cariocão",
        "conmebol.libertadores": "Libertadores", "conmebol.sudamericana": "Sul-Americana",
        "eng.1": "Premier League (Ing)", "esp.1": "LaLiga (Esp)", "esp.copa_del_rey": "Copa del Rey (Esp)",
        "ita.1": "Série A (Ita)", "ita.coppa_italia": "Coppa Italia (Ita)", "ger.1": "Bundesliga (Ale)",
        "por.1": "Liga Portugal (Por)", "uefa.champions": "Champions League",
        "ned.1": "Eredivisie (Hol)", "aut.1": "Bundesliga (Aut)", "bel.1": "Pro League (Bel)", "usa.1": "MLS (EUA)"
    }

    jogos_hoje = []

    for liga_id, liga_nome in ligas.items():
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{liga_id}/scoreboard"
        try:
            res = requests.get(url, timeout=15)
            data = res.json()
            eventos = data.get('events', [])
            for evento in eventos:
                # Extrair data do jogo e ajustar fuso
                data_iso = evento.get('date')
                dt_utc = datetime.fromisoformat(data_iso.replace('Z', ''))
                dt_br = dt_utc - timedelta(hours=3)
                
                # TRAVA: Só adiciona se o jogo for HOJE
                if dt_br.strftime('%Y-%m-%d') == hoje_br:
                    nome_bruto = evento.get('name')
                    nome_jogo = nome_bruto.replace(' at ', ' x ').replace(' & ', ' x ')
                    link_estatistica = evento.get('links')[0].get('href')
                    
                    jogos_hoje.append({
                        "liga": liga_nome,
                        "jogo": nome_jogo,
                        "hora": dt_br.strftime("%H:%M"),
                        "link": link_estatistica
                    })
        except:
            continue

    if len(jogos_hoje) < 10:
        msg_aviso = f"⚠️ *Aviso:* Encontrados apenas {len(jogos_hoje)} jogos para hoje ({hoje_br}). Impossível montar múltipla de 10 jogos."
        enviar_telegram(msg_aviso)
        return

    # --- LOOP DE CALIBRAGEM (Tenta até 2000 combinações) ---
    tentativas = 0
    while tentativas < 2000:
        selecao = random.sample(jogos_hoje, 10)
        odd_total = 1.0
        bilhete_final = []

        for jogo in selecao:
            palpite, conf, odd_est = definir_palpite_estrategico()
            odd_total *= odd_est
            bilhete_final.append({**jogo, "aposta": palpite, "odd": odd_est})

        # Verifica se a odd está no intervalo desejado (90-110)
        if 90 <= odd_total <= 110:
            msg = f"🎯 *BILHETE DO DIA: ODD {odd_total:.2f}*\n"
            msg += f"_Apenas jogos de HOJE ({hoje_br}) | Alvo: 100x_\n\n"
            
            for i, j in enumerate(bilhete_final, 1):
                msg += f"{i}. 🏟️ *{j['jogo']}*\n🕒 {j['hora']} | _{j['liga']}_\n🎯 *{j['aposta']}*\n📊 [Estatísticas]({j['link']})\n\n"
            
            msg += "---\n"
            msg += "💸 *APOSTAR AGORA:*\n"
            msg += "🔹 [Ir para Bet365](https://www.bet365.com/#/AS/B1/)\n"
            msg += "🔸 [Ir para Betano](https://br.betano.com/sport/futebol/)\n\n"
            msg += "⚠️ _Odds estimadas. Confira no site das casas._"
            
            enviar_telegram(msg)
            print(f"Sucesso! Odd {odd_total:.2f} enviada em {tentativas} tentativas.")
            return
        
        tentativas += 1

    print("Não foi possível calibrar a Odd no intervalo solicitado com os jogos de hoje.")

if __name__ == "__main__":
    executar_robo()
    
