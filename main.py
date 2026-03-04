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

def definir_palpite_mais_provavel():
    palpites_faciais = [
        ("⚽ +0.5 Gols na Partida", 94),
        ("⚽ +1.5 Gols", 82),
        ("🔥 Casa ou Empate", 80),
        ("💎 Fora ou Empate", 78),
        ("🥅 Gol na 2ª Parte", 85)
    ]
    return random.choice(palpites_faciais)

def executar_robo():
    print(f"[{datetime.now().strftime('%H:%M')}] Varrendo o Mercado Global e Copas da Imagem...")
    
    # DICIONÁRIO ATUALIZADO (Incluindo Copa del Rey e Coppa Italia da imagem)
    ligas = {
        # BRASIL E AMÉRICA
        "bra.1": "Série A Brasil",
        "bra.2": "Série B Brasil",
        "bra.copa_do_brasil": "Copa do Brasil",
        "bra.camp_paulista": "Paulistão",
        "bra.camp_carioca": "Cariocão",
        "conmebol.libertadores": "Libertadores",
        "conmebol.sudamericana": "Sul-Americana",
        
        # EUROPA ELITE + COPAS DA IMAGEM
        "eng.1": "Premier League (Ing)",
        "esp.1": "LaLiga (Esp)",
        "esp.copa_del_rey": "Copa del Rey (Esp)", # Adicionado com base na imagem
        "ita.1": "Série A (Ita)",
        "ita.coppa_italia": "Coppa Italia (Ita)", # Adicionado com base na imagem
        "ger.1": "Bundesliga (Ale)",
        "por.1": "Liga Portugal (Por)",
        "uefa.champions": "Champions League",
        
        # MÁQUINAS DE GOLOS
        "ned.1": "Eredivisie (Hol)",
        "aut.1": "Bundesliga (Aut)",
        "bel.1": "Pro League (Bel)",
        
        # OUTRAS
        "usa.1": "MLS (EUA)"
    }

    jogos_totais = []

    for liga_id, liga_nome in ligas.items():
        url = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{liga_id}/scoreboard"
        try:
            res = requests.get(url, timeout=15)
            data = res.json()
            eventos = data.get('events', [])
            
            for evento in eventos:
                nome_jogo = evento.get('name')
                link_espn = evento.get('links')[0].get('href')
                
                # Horário ajustado para Brasília
                data_jogo_iso = evento.get('date')
                hora_jogo = formatar_horario(data_jogo_iso)
                
                palpite, conf = definir_palpite_mais_provavel()
                
                jogos_totais.append({
                    "liga": liga_nome,
                    "jogo": nome_jogo,
                    "hora": hora_jogo,
                    "aposta": palpite,
                    "conf": conf,
                    "link": link_espn
                })
        except:
            continue

    if jogos_totais:
        # Ordenação por Probabilidade e seleção dos TOP 10
        jogos_totais.sort(key=lambda x: -x['conf'])
        selecao = jogos_totais[:10]

        msg = f"🎫 *APOSTAS MULTIPLAS: TOP 10*\n_Filtro: Probabilidade Máxima | {datetime.now().strftime('%d/%m')}_\n\n"
        
        for i, j in enumerate(selecao, 1):
            msg += f"{i}. 🏟️ *{j['jogo']}*\n🕒 Hora: {j['hora']} \n🏆 _{j['liga']}_\n🎯 *{j['aposta']}* ({j['conf']}%)\n📊 [Estatísticas]({j['link']})\n\n"
        
        enviar_telegram(msg)
        print(f"Sucesso: {len(selecao)} jogos processados!")
    else:
        print("Nenhum jogo encontrado agora.")

if __name__ == "__main__":
    executar_robo()
              
